"""
Android native barcode scanner backend implementation using CameraX and Google ML Kit.

This module provides hardware-accelerated 1D/2D barcode scanning on Android devices
using AndroidX CameraX (`androidx.camera`) and Google ML Kit (`com.google.mlkit:barcode-scanning`).
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from toga_barcode_scanner.factory import BaseBarcodeScannerBackend
from toga_barcode_scanner.models import (
    BarcodeFormat,
    CameraFacing,
    ScanMode,
)

if TYPE_CHECKING:
    from toga_barcode_scanner.core import BarcodeScanner

# Android Permission Constants
PERMISSION_GRANTED = 0
PERMISSION_DENIED = -1
CAMERA_PERMISSION_REQUEST_CODE = 8192

# ML Kit Barcode Format Constants (from com.google.mlkit.vision.barcode.common.Barcode)
MLKIT_FORMAT_ALL_FORMATS = 0
MLKIT_FORMAT_CODE_128 = 1
MLKIT_FORMAT_CODE_39 = 2
MLKIT_FORMAT_DATA_MATRIX = 16
MLKIT_FORMAT_EAN_13 = 32
MLKIT_FORMAT_EAN_8 = 64
MLKIT_FORMAT_QR_CODE = 256
MLKIT_FORMAT_UPC_A = 512
MLKIT_FORMAT_UPC_E = 1024
MLKIT_FORMAT_AZTEC = 4096

FORMAT_TO_MLKIT: Dict[BarcodeFormat, int] = {
    BarcodeFormat.UPC_A: MLKIT_FORMAT_UPC_A,
    BarcodeFormat.UPC_E: MLKIT_FORMAT_UPC_E,
    BarcodeFormat.EAN_8: MLKIT_FORMAT_EAN_8,
    BarcodeFormat.EAN_13: MLKIT_FORMAT_EAN_13,
    BarcodeFormat.CODE_39: MLKIT_FORMAT_CODE_39,
    BarcodeFormat.CODE_128: MLKIT_FORMAT_CODE_128,
    BarcodeFormat.QR_CODE: MLKIT_FORMAT_QR_CODE,
    BarcodeFormat.DATA_MATRIX: MLKIT_FORMAT_DATA_MATRIX,
    BarcodeFormat.AZTEC: MLKIT_FORMAT_AZTEC,
    BarcodeFormat.ALL: MLKIT_FORMAT_ALL_FORMATS,
}

MLKIT_TO_FORMAT: Dict[int, BarcodeFormat] = {
    MLKIT_FORMAT_UPC_A: BarcodeFormat.UPC_A,
    MLKIT_FORMAT_UPC_E: BarcodeFormat.UPC_E,
    MLKIT_FORMAT_EAN_8: BarcodeFormat.EAN_8,
    MLKIT_FORMAT_EAN_13: BarcodeFormat.EAN_13,
    MLKIT_FORMAT_CODE_39: BarcodeFormat.CODE_39,
    MLKIT_FORMAT_CODE_128: BarcodeFormat.CODE_128,
    MLKIT_FORMAT_QR_CODE: BarcodeFormat.QR_CODE,
    MLKIT_FORMAT_DATA_MATRIX: BarcodeFormat.DATA_MATRIX,
    MLKIT_FORMAT_AZTEC: BarcodeFormat.AZTEC,
}

try:
    from java import (  # type: ignore[import-not-found,import-untyped]
        dynamic_proxy,
        jclass,
    )

    Manifest = jclass("android.Manifest")
    PackageManager = jclass("android.content.pm.PackageManager")
    ContextCompat = jclass("androidx.core.content.ContextCompat")
    ActivityCompat = jclass("androidx.core.app.ActivityCompat")

    ProcessCameraProvider = jclass("androidx.camera.lifecycle.ProcessCameraProvider")
    CameraSelector = jclass("androidx.camera.core.CameraSelector")
    Preview = jclass("androidx.camera.core.Preview")
    ImageAnalysis = jclass("androidx.camera.core.ImageAnalysis")
    InputImage = jclass("com.google.mlkit.vision.common.InputImage")
    BarcodeScanning = jclass("com.google.mlkit.vision.barcode.BarcodeScanning")
    BarcodeScannerOptions = jclass(
        "com.google.mlkit.vision.barcode.BarcodeScannerOptions"
    )

    FrameLayout = jclass("android.widget.FrameLayout")
    Button = jclass("android.widget.Button")
    Color = jclass("android.graphics.Color")
    Executors = jclass("java.util.concurrent.Executors")

    HAS_CHAQUOPY = True
except Exception:
    HAS_CHAQUOPY = False


def process_android_barcodes(backend: Any, barcode_list: Any) -> None:
    """
    Process decoded Google ML Kit barcode objects and dispatch results.

    :param backend: Active AndroidBarcodeScanner instance.
    :param barcode_list: Collection/List of ML Kit Barcode objects.
    """
    if not backend or not barcode_list:
        return

    # Handle iterable or size/get based collections
    count = getattr(barcode_list, "size", None)
    items = (
        [barcode_list.get(i) for i in range(count())]
        if callable(count)
        else barcode_list
    )

    for barcode in items:
        raw_value = getattr(
            barcode, "getRawValue", lambda: getattr(barcode, "rawValue", None)
        )()
        if not raw_value:
            continue

        format_int = getattr(
            barcode,
            "getFormat",
            lambda: getattr(barcode, "format", MLKIT_FORMAT_ALL_FORMATS),
        )()
        detected_format = MLKIT_TO_FORMAT.get(int(format_int), BarcodeFormat.CODE_128)

        # Normalized or pixel bounding box
        rect = getattr(
            barcode, "getBoundingBox", lambda: getattr(barcode, "boundingBox", None)
        )()
        bounding_box: Optional[Tuple[float, float, float, float]] = None
        if rect:
            try:
                bounding_box = (
                    float(rect.left),
                    float(rect.top),
                    float(
                        rect.width()
                        if callable(getattr(rect, "width", None))
                        else rect.width
                    ),
                    float(
                        rect.height()
                        if callable(getattr(rect, "height", None))
                        else rect.height
                    ),
                )
            except Exception:
                bounding_box = None

        backend.interface._dispatch_barcode(
            raw_value=str(raw_value),
            format_=detected_format,
            bounding_box=bounding_box,
        )


class AndroidBarcodeScanner(BaseBarcodeScannerBackend):
    """
    Android native barcode scanner implementation using CameraX and Google ML Kit.
    """

    def __init__(self, interface: BarcodeScanner) -> None:
        """
        Initialize the Android scanner backend.

        :param interface: The BarcodeScanner core interface instance.
        """
        super().__init__(interface)
        self._camera: Any = None
        self._camera_provider: Any = None
        self._overlay_layout: Any = None
        self._analysis_executor: Any = None

    def _get_activity(self) -> Any:
        """
        Retrieve the current Android Activity from the host Toga application.
        """
        if self.interface.app and hasattr(self.interface.app, "_impl"):
            return getattr(self.interface.app._impl, "native", None)
        return None

    def is_permission_granted(self) -> bool:
        """
        Check if the app has been granted runtime CAMERA permission.

        :return: True if authorized, False otherwise.
        """
        if not HAS_CHAQUOPY:
            return False

        try:
            activity = self._get_activity()
            if not activity:
                return False

            permission_status = ContextCompat.checkSelfPermission(
                activity, Manifest.permission.CAMERA
            )
            return permission_status == PackageManager.PERMISSION_GRANTED
        except Exception:
            return False

    async def request_permission(self) -> bool:
        """
        Asynchronously prompt user for Android runtime camera permission.

        :return: True if granted, False if denied.
        """
        if not HAS_CHAQUOPY:
            return False

        try:
            if self.is_permission_granted():
                return True

            activity = self._get_activity()
            if not activity:
                return False

            ActivityCompat.requestPermissions(
                activity,
                [Manifest.permission.CAMERA],
                CAMERA_PERMISSION_REQUEST_CODE,
            )
            # In headless or callback bridge scenarios, check updated status
            return self.is_permission_granted()
        except Exception:
            return False

    def _build_mlkit_options(self) -> Any:
        """
        Build BarcodeScannerOptions configured for target BarcodeFormats.
        """
        if not HAS_CHAQUOPY:
            return None

        builder = BarcodeScannerOptions.Builder()
        if BarcodeFormat.ALL in self.interface.formats:
            builder.setBarcodeFormats(MLKIT_FORMAT_ALL_FORMATS)
        else:
            formats = [
                FORMAT_TO_MLKIT[fmt]
                for fmt in self.interface.formats
                if fmt in FORMAT_TO_MLKIT
            ]
            if formats:
                first = formats[0]
                rest = formats[1:]
                builder.setBarcodeFormats(first, *rest)
        return builder.build()

    def start_scan(self, parent_window: Optional[Any] = None) -> None:
        """
        Start CameraX video stream and bind ML Kit ImageAnalysis analyzer.

        :param parent_window: Optional parent Toga window.
        """
        if self._is_scanning:
            return

        if not self.is_permission_granted():
            self.interface._dispatch_error("PERMISSION_DENIED")
            return

        if not HAS_CHAQUOPY:
            self.interface._dispatch_error("ANDROID_RUNTIME_UNAVAILABLE")
            return

        try:
            activity = self._get_activity()
            if not activity:
                self.interface._dispatch_error("ACTIVITY_UNAVAILABLE")
                return

            self._analysis_executor = Executors.newSingleThreadExecutor()
            camera_provider_future = ProcessCameraProvider.getInstance(activity)

            def on_provider_ready():
                try:
                    self._camera_provider = camera_provider_future.get()

                    # Select Camera Facing
                    selector_builder = CameraSelector.Builder()
                    if self.interface.camera_facing == CameraFacing.FRONT:
                        selector_builder.requireLensFacing(
                            CameraSelector.LENS_FACING_FRONT
                        )
                    else:
                        selector_builder.requireLensFacing(
                            CameraSelector.LENS_FACING_BACK
                        )
                    camera_selector = selector_builder.build()

                    # Configure ImageAnalysis use case
                    mlkit_options = self._build_mlkit_options()
                    scanner_client = BarcodeScanning.getClient(mlkit_options)

                    analysis_use_case = (
                        ImageAnalysis.Builder()
                        .setBackpressureStrategy(
                            ImageAnalysis.STRATEGY_KEEP_ONLY_LATEST
                        )
                        .build()
                    )

                    class AnalyzerProxy(dynamic_proxy(ImageAnalysis.Analyzer)):
                        def analyze(self, image_proxy):
                            media_image = image_proxy.getImage()
                            if media_image:
                                rotation = (
                                    image_proxy.getImageInfo().getRotationDegrees()
                                )
                                input_image = InputImage.fromMediaImage(
                                    media_image, rotation
                                )

                                def on_success(barcodes):
                                    process_android_barcodes(self, barcodes)
                                    image_proxy.close()

                                def on_failure(exc):
                                    image_proxy.close()

                                scanner_client.process(
                                    input_image
                                ).addOnSuccessListener(on_success).addOnFailureListener(
                                    on_failure
                                )
                            else:
                                image_proxy.close()

                    analysis_use_case.setAnalyzer(
                        self._analysis_executor, AnalyzerProxy()
                    )

                    self._camera_provider.unbindAll()
                    self._camera = self._camera_provider.bindToLifecycle(
                        activity, camera_selector, analysis_use_case
                    )
                    self._is_scanning = True

                except Exception as inner_exc:
                    self.interface._dispatch_error(f"CAMERAX_BIND_ERROR: {inner_exc}")

            camera_provider_future.addListener(
                on_provider_ready, ContextCompat.getMainExecutor(activity)
            )

        except Exception as exc:
            self.interface._dispatch_error(f"ANDROID_CAPTURE_ERROR: {exc}")

    def stop_scan(self) -> None:
        """
        Unbind CameraX use cases, release executor, and dismiss overlay.
        """
        if not self._is_scanning:
            return

        if self._camera_provider:
            try:
                self._camera_provider.unbindAll()
            except Exception:
                pass

        if self._analysis_executor:
            try:
                self._analysis_executor.shutdown()
            except Exception:
                pass
            self._analysis_executor = None

        self.toggle_torch(False)
        self._torch_enabled = False
        self._is_scanning = False

    def toggle_torch(self, enabled: bool) -> None:
        """
        Toggle Android device torch / flashlight.

        :param enabled: True to enable torch, False to disable.
        """
        if not self._camera:
            self._torch_enabled = enabled
            return

        try:
            camera_control = self._camera.getCameraControl()
            if camera_control:
                camera_control.enableTorch(bool(enabled))
                self._torch_enabled = enabled
        except Exception:
            pass
