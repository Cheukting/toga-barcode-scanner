"""
iOS native barcode scanner backend implementation using AVFoundation and rubicon-objc.

This module provides hardware-accelerated 1D/2D barcode scanning on iOS devices
by orchestrating AVCaptureSession, AVCaptureMetadataOutput, and modal UIKit viewfinder overlays.
"""

from __future__ import annotations

import asyncio
import ctypes
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from toga_barcode_scanner.factory import BaseBarcodeScannerBackend
from toga_barcode_scanner.models import (
    BarcodeFormat,
    CameraFacing,
    ScanMode,
)

if TYPE_CHECKING:
    from toga_barcode_scanner.core import BarcodeScanner

try:
    import rubicon.objc  # type: ignore[import-untyped]
    from rubicon.objc import (  # type: ignore[import-untyped]
        Block,
        CGFloat,
        CGPoint,
        CGRect,
        CGSize,
        NSObject,
        ObjCClass,
        ObjCProtocol,
        objc_method,
        py_from_ns,
    )

    # Attempt to load iOS/macOS frameworks safely
    for fw in ("AVFoundation", "UIKit", "CoreGraphics"):
        try:
            ctypes.cdll.LoadLibrary(f"/System/Library/Frameworks/{fw}.framework/{fw}")
        except Exception:
            pass

    try:
        AVCaptureSession = ObjCClass("AVCaptureSession")
        AVCaptureDevice = ObjCClass("AVCaptureDevice")
        AVCaptureDeviceInput = ObjCClass("AVCaptureDeviceInput")
        AVCaptureMetadataOutput = ObjCClass("AVCaptureMetadataOutput")
        AVCaptureVideoPreviewLayer = ObjCClass("AVCaptureVideoPreviewLayer")
    except Exception:
        pass

    try:
        UIViewController = ObjCClass("UIViewController")
        UIView = ObjCClass("UIView")
        UIButton = ObjCClass("UIButton")
        UIColor = ObjCClass("UIColor")
        UIFont = ObjCClass("UIFont")
        UIApplication = ObjCClass("UIApplication")
    except Exception:
        pass

    try:
        dispatch_get_main_queue = ctypes.CDLL(
            None
        ).dispatch_get_main_queue  # type: ignore[arg-type]
        dispatch_get_main_queue.restype = ctypes.c_void_p
    except Exception:
        pass

    HAS_RUBICON_OBJC = True
except Exception:
    HAS_RUBICON_OBJC = False


# AVAuthorizationStatus Constants
AVAuthorizationStatusNotDetermined = 0
AVAuthorizationStatusRestricted = 1
AVAuthorizationStatusDenied = 2
AVAuthorizationStatusAuthorized = 3

# AVCaptureTorchMode Constants
AVCaptureTorchModeOff = 0
AVCaptureTorchModeOn = 1
AVCaptureTorchModeAuto = 2

# AVCaptureDevicePosition Constants
AVCaptureDevicePositionUnspecified = 0
AVCaptureDevicePositionBack = 1
AVCaptureDevicePositionFront = 2

# Native AVFoundation Metadata String Constants
AVMetadataObjectTypeUPCE = "org.gs1.UPC-E"
AVMetadataObjectTypeEAN8 = "org.gs1.EAN-8"
AVMetadataObjectTypeEAN13 = "org.gs1.EAN-13"
AVMetadataObjectTypeQRCode = "org.iso.QRCode"
AVMetadataObjectTypeCode39 = "org.iso.Code39"
AVMetadataObjectTypeCode128 = "org.iso.Code128"
AVMetadataObjectTypeDataMatrix = "org.iso.DataMatrix"
AVMetadataObjectTypeAztec = "org.iso.Aztec"

# Mapping between Python BarcodeFormat enums and AVMetadataObjectTypes
FORMAT_TO_AV_METADATA: Dict[BarcodeFormat, str] = {
    BarcodeFormat.UPC_E: AVMetadataObjectTypeUPCE,
    BarcodeFormat.EAN_8: AVMetadataObjectTypeEAN8,
    BarcodeFormat.EAN_13: AVMetadataObjectTypeEAN13,
    BarcodeFormat.UPC_A: AVMetadataObjectTypeEAN13,  # UPC-A is reported within EAN-13 in AVFoundation
    BarcodeFormat.QR_CODE: AVMetadataObjectTypeQRCode,
    BarcodeFormat.CODE_39: AVMetadataObjectTypeCode39,
    BarcodeFormat.CODE_128: AVMetadataObjectTypeCode128,
    BarcodeFormat.DATA_MATRIX: AVMetadataObjectTypeDataMatrix,
    BarcodeFormat.AZTEC: AVMetadataObjectTypeAztec,
}

AV_METADATA_TO_FORMAT: Dict[str, BarcodeFormat] = {
    AVMetadataObjectTypeUPCE: BarcodeFormat.UPC_E,
    AVMetadataObjectTypeEAN8: BarcodeFormat.EAN_8,
    AVMetadataObjectTypeEAN13: BarcodeFormat.EAN_13,
    AVMetadataObjectTypeQRCode: BarcodeFormat.QR_CODE,
    AVMetadataObjectTypeCode39: BarcodeFormat.CODE_39,
    AVMetadataObjectTypeCode128: BarcodeFormat.CODE_128,
    AVMetadataObjectTypeDataMatrix: BarcodeFormat.DATA_MATRIX,
    AVMetadataObjectTypeAztec: BarcodeFormat.AZTEC,
}


def process_ios_metadata_objects(backend: Any, metadataObjects: Any) -> None:
    """
    Parse native AVMetadataMachineReadableCodeObject list and dispatch to coordinator.

    :param backend: Active iOSBarcodeScanner instance.
    :param metadataObjects: Native NSArray of metadata objects.
    """
    if not backend or not metadataObjects:
        return

    count = getattr(metadataObjects, "count", 0)
    for i in range(count):
        obj = metadataObjects.objectAtIndex_(i)
        raw_value = str(obj.stringValue) if getattr(obj, "stringValue", None) else None
        type_str = str(getattr(obj, "type", ""))

        if not raw_value:
            continue

        fmt = AV_METADATA_TO_FORMAT.get(type_str, BarcodeFormat.CODE_128)

        # Special-case UPC-A normalization if detected as EAN-13 with leading zero
        if (
            fmt == BarcodeFormat.EAN_13
            and len(raw_value) == 13
            and raw_value.startswith("0")
        ):
            if (
                BarcodeFormat.UPC_A in backend.interface.formats
                or BarcodeFormat.ALL in backend.interface.formats
            ):
                fmt = BarcodeFormat.UPC_A
                raw_value = raw_value[1:]

        # Extract normalized bounding box if present
        bounds = getattr(obj, "bounds", None)
        bounding_box: Optional[Tuple[float, float, float, float]] = None
        if bounds:
            try:
                bounding_box = (
                    float(bounds.origin.x),
                    float(bounds.origin.y),
                    float(bounds.size.width),
                    float(bounds.size.height),
                )
            except Exception:
                bounding_box = None

        backend.interface._dispatch_barcode(
            raw_value=raw_value,
            format_=fmt,
            bounding_box=bounding_box,
        )


if HAS_RUBICON_OBJC:

    class BarcodeCaptureDelegate(NSObject):  # type: ignore[misc]
        """
        Objective-C delegate implementing AVCaptureMetadataOutputObjectsDelegate.
        Marshals detected barcode metadata objects into Python callbacks.
        """

        @objc_method
        def captureOutput_didOutputMetadataObjects_fromConnection_(
            self, output, metadataObjects, connection
        ) -> None:
            """
            Invoked by AVFoundation when one or more metadata objects are detected in a video frame.
            """
            backend = getattr(self, "backend", None)
            if backend:
                process_ios_metadata_objects(backend, metadataObjects)

else:

    class BarcodeCaptureDelegate:  # type: ignore[no-redef]
        """Fallback stub when rubicon-objc is not installed."""

        def __init__(self) -> None:
            self.backend = None


class iOSBarcodeScanner(BaseBarcodeScannerBackend):
    """
    iOS backend for `BarcodeScanner` built on Apple AVFoundation and UIKit.
    """

    def __init__(self, interface: BarcodeScanner) -> None:
        """
        Initialize the iOS scanner backend.

        :param interface: The BarcodeScanner core interface instance.
        """
        super().__init__(interface)
        self._session: Any = None
        self._device: Any = None
        self._preview_layer: Any = None
        self._view_controller: Any = None
        self._delegate: Any = None

    def is_permission_granted(self) -> bool:
        """
        Check if the app is currently authorized to use the camera.

        :return: True if authorized, False otherwise.
        """
        if not HAS_RUBICON_OBJC:
            return False

        try:
            status = AVCaptureDevice.authorizationStatusForMediaType_("vide")
            return status == AVAuthorizationStatusAuthorized
        except Exception:
            return False

    async def request_permission(self) -> bool:
        """
        Asynchronously prompt the user for camera access authorization.

        :return: True if granted, False if denied.
        """
        if not HAS_RUBICON_OBJC:
            return False

        try:
            status = AVCaptureDevice.authorizationStatusForMediaType_("vide")
            if status == AVAuthorizationStatusAuthorized:
                return True
            elif status in (
                AVAuthorizationStatusDenied,
                AVAuthorizationStatusRestricted,
            ):
                return False

            loop = asyncio.get_running_loop()
            future: asyncio.Future[bool] = loop.create_future()

            def completion_handler(granted: bool) -> None:
                loop.call_soon_threadsafe(future.set_result, bool(granted))

            handler_block = Block(completion_handler, None, ctypes.c_bool)
            AVCaptureDevice.requestAccessForMediaType_completionHandler_(
                "vide", handler_block
            )

            return await future
        except Exception:
            return False

    def _get_target_metadata_types(self) -> List[str]:
        """
        Convert configured `BarcodeFormat` list into AVFoundation metadata type identifiers.
        """
        if BarcodeFormat.ALL in self.interface.formats or not self.interface.formats:
            return list(FORMAT_TO_AV_METADATA.values())

        types = []
        for fmt in self.interface.formats:
            av_type = FORMAT_TO_AV_METADATA.get(fmt)
            if av_type and av_type not in types:
                types.append(av_type)
        return types

    def _get_camera_device(self) -> Any:
        """
        Acquire the target camera device matching `camera_facing`.
        """
        position = (
            AVCaptureDevicePositionFront
            if self.interface.camera_facing == CameraFacing.FRONT
            else AVCaptureDevicePositionBack
        )

        try:
            # Discovery session / default device fallback
            device = AVCaptureDevice.defaultDeviceWithMediaType_("vide")
            devices = AVCaptureDevice.devicesWithMediaType_("vide")
            count = devices.count
            for i in range(count):
                d = devices.objectAtIndex_(i)
                if d.position == position:
                    return d
            return device
        except Exception:
            return None

    def start_scan(self, parent_window: Optional[Any] = None) -> None:
        """
        Start camera session and present the modal scanner view controller.

        :param parent_window: Optional parent Toga window.
        """
        if self._is_scanning:
            return

        if not self.is_permission_granted():
            self.interface._dispatch_error("PERMISSION_DENIED")
            return

        try:
            self._session = AVCaptureSession.alloc().init()
            self._device = self._get_camera_device()

            if not self._device:
                self.interface._dispatch_error("CAMERA_UNAVAILABLE")
                return

            error = ctypes.c_void_p()
            input_device = AVCaptureDeviceInput.deviceInputWithDevice_error_(
                self._device, ctypes.byref(error)
            )

            if self._session.canAddInput_(input_device) and input_device is not None:
                self._session.addInput_(input_device)
            else:
                self.interface._dispatch_error("CAMERA_INPUT_FAILED")
                return

            metadata_output = AVCaptureMetadataOutput.alloc().init()
            if self._session.canAddOutput_(metadata_output):
                self._session.addOutput_(metadata_output)
            else:
                self.interface._dispatch_error("CAMERA_OUTPUT_FAILED")
                return

            # Setup metadata delegate
            self._delegate = BarcodeCaptureDelegate.alloc().init()
            self._delegate.backend = self

            main_queue = dispatch_get_main_queue()
            metadata_output.setMetadataObjectsDelegate_queue_(
                self._delegate, main_queue
            )

            # Configure symbology types
            target_types = self._get_target_metadata_types()
            metadata_output.metadataObjectTypes = target_types

            # Construct View Controller and Overlay
            self._construct_viewfinder(parent_window)

            self._session.startRunning()
            self._is_scanning = True

        except Exception as exc:
            self.interface._dispatch_error(f"IOS_CAPTURE_ERROR: {exc}")

    def _construct_viewfinder(self, parent_window: Optional[Any]) -> None:
        """
        Build and present modal UIViewController with preview layer, reticle, and action buttons.
        """
        try:
            self._view_controller = UIViewController.alloc().init()
            view = self._view_controller.view
            view.backgroundColor = UIColor.blackColor

            # Camera preview layer
            self._preview_layer = AVCaptureVideoPreviewLayer.layerWithSession_(
                self._session
            )
            self._preview_layer.videoGravity = "AVLayerVideoGravityResizeAspectFill"
            self._preview_layer.frame = view.bounds
            view.layer.addSublayer_(self._preview_layer)

            # Reticle frame view
            if self.interface.show_overlay:
                reticle = UIView.alloc().initWithFrame_(
                    CGRect(
                        CGPoint(
                            (view.bounds.size.width - 260) / 2,
                            (view.bounds.size.height - 260) / 2,
                        ),
                        CGSize(260, 260),
                    )
                )
                reticle.layer.borderColor = UIColor.greenColor.CGColor
                reticle.layer.borderWidth = 2.0
                reticle.layer.cornerRadius = 8.0
                reticle.userInteractionEnabled = False
                view.addSubview_(reticle)

            # Close button
            close_btn = UIButton.buttonWithType_(0)  # UIButtonTypeCustom
            close_btn.frame = CGRect(CGPoint(20, 50), CGSize(44, 44))
            close_btn.setTitle_forState_("✕", 0)  # UIControlStateNormal
            close_btn.titleLabel.font = UIFont.boldSystemFontOfSize_(24)
            close_btn.setTitleColor_forState_(UIColor.whiteColor, 0)
            view.addSubview_(close_btn)

            # Torch toggle button
            if self._device and getattr(self._device, "hasTorch", False):
                torch_btn = UIButton.buttonWithType_(0)
                torch_btn.frame = CGRect(
                    CGPoint(view.bounds.size.width - 64, 50), CGSize(44, 44)
                )
                torch_btn.setTitle_forState_("⚡", 0)
                torch_btn.titleLabel.font = UIFont.systemFontOfSize_(22)
                torch_btn.setTitleColor_forState_(UIColor.whiteColor, 0)
                view.addSubview_(torch_btn)

            # Present view controller
            app_instance = UIApplication.sharedApplication
            key_window = app_instance.keyWindow
            root_vc = key_window.rootViewController if key_window else None
            if root_vc:
                root_vc.presentViewController_animated_completion_(
                    self._view_controller, True, None
                )
        except Exception:
            pass

    def stop_scan(self) -> None:
        """
        Stop AVCaptureSession, dismiss modal viewfinder, and reset torch.
        """
        if not self._is_scanning:
            return

        if self._session and getattr(self._session, "isRunning", False):
            try:
                self._session.stopRunning()
            except Exception:
                pass

        self.toggle_torch(False)
        self._torch_enabled = False

        if self._view_controller:
            try:
                self._view_controller.dismissViewControllerAnimated_completion_(
                    True, None
                )
            except Exception:
                pass
            self._view_controller = None

        self._is_scanning = False

    def toggle_torch(self, enabled: bool) -> None:
        """
        Toggle hardware flashlight / torch.

        :param enabled: True to turn on torch, False to turn off.
        """
        if not self._device or not getattr(self._device, "hasTorch", False):
            self._torch_enabled = enabled
            return

        try:
            error = ctypes.c_void_p()
            if self._device.lockForConfiguration_(ctypes.byref(error)):
                mode = AVCaptureTorchModeOn if enabled else AVCaptureTorchModeOff
                self._device.torchMode = mode
                self._device.unlockForConfiguration()
                self._torch_enabled = enabled
        except Exception:
            pass
