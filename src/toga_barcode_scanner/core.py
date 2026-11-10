"""
Core BarcodeScanner hardware plugin interface and event coordinator.

This module provides the central public API class `BarcodeScanner` for the
Toga / BeeWare ecosystem. It coordinates scanning lifecycle, debouncing,
symbology format filtering, and callback dispatching while delegating platform-specific
camera hardware operations to the active backend.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any, Callable, List, Optional, Tuple

from toga_barcode_scanner.factory import BaseBarcodeScannerBackend, get_platform_scanner
from toga_barcode_scanner.models import (
    BarcodeFormat,
    BarcodeResult,
    CameraFacing,
    ScanMode,
)

if TYPE_CHECKING:
    import toga


class BarcodeScanner:
    """
    Cross-platform barcode scanner service for Toga / BeeWare applications.

    Orchestrates camera permission flows, capture session controls, flashlight toggles,
    and barcode detection callbacks with configurable debouncing and format filtering.
    """

    def __init__(
        self,
        app: Optional[Any] = None,
        on_barcode: Optional[Callable[[BarcodeResult], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
        formats: Optional[List[BarcodeFormat]] = None,
        camera_facing: CameraFacing = CameraFacing.BACK,
        scan_mode: ScanMode = ScanMode.SINGLE_SHOT,
        show_overlay: bool = True,
        beep_on_scan: bool = True,
        vibrate_on_scan: bool = True,
        debounce_ms: int = 300,
        backend: Optional[str | BaseBarcodeScannerBackend] = None,
    ) -> None:
        """
        Initialize the BarcodeScanner service.

        :param app: Optional reference to the host `toga.App`.
        :param on_barcode: Callback invoked when a valid barcode is decoded.
        :param on_error: Callback invoked when an error or permission denial occurs.
        :param formats: List of BarcodeFormat symbologies to detect (defaults to [BarcodeFormat.ALL]).
        :param camera_facing: Hardware camera sensor to activate (CameraFacing.BACK or CameraFacing.FRONT).
        :param scan_mode: ScanMode.SINGLE_SHOT (auto-dismiss on first read) or ScanMode.CONTINUOUS.
        :param show_overlay: Whether to present the native viewfinder reticle overlay.
        :param beep_on_scan: Whether to trigger an audible cue upon barcode detection.
        :param vibrate_on_scan: Whether to trigger haptic feedback upon barcode detection.
        :param debounce_ms: Debounce threshold in milliseconds to eliminate duplicate scans.
        :param backend: Optional explicit backend override (e.g. 'dummy', 'ios', 'android').
        """
        self.app = app
        self.on_barcode = on_barcode
        self.on_error = on_error
        self.formats = formats or [BarcodeFormat.ALL]
        self.camera_facing = camera_facing
        self.scan_mode = scan_mode
        self.show_overlay = show_overlay
        self.beep_on_scan = beep_on_scan
        self.vibrate_on_scan = vibrate_on_scan
        self.debounce_ms = debounce_ms

        self._last_scan_time: float = 0.0
        self._last_scanned_value: Optional[str] = None

        # Initialize the platform-specific backend implementation
        self._impl: BaseBarcodeScannerBackend = get_platform_scanner(
            self, backend=backend
        )

    @property
    def is_scanning(self) -> bool:
        """Returns True if the camera capture session is currently active."""
        return self._impl.is_scanning

    @property
    def is_torch_enabled(self) -> bool:
        """Returns True if the camera flashlight is currently enabled."""
        return self._impl.is_torch_enabled

    def is_permission_granted(self) -> bool:
        """
        Checks if camera permission has been granted by the host operating system.

        :return: True if authorized, False otherwise.
        """
        return self._impl.is_permission_granted()

    async def request_permission(self) -> bool:
        """
        Asynchronously requests camera access permissions from the host OS.

        :return: True if granted, False if denied.
        """
        return await self._impl.request_permission()

    def start_scan(self, parent_window: Optional[Any] = None) -> None:
        """
        Activates the camera view and begins analyzing frames for barcodes.

        :param parent_window: Optional parent Toga window used for modal presentation.
        """
        self._impl.start_scan(parent_window=parent_window)

    def stop_scan(self) -> None:
        """
        Deactivates camera capture and dismisses the viewfinder overlay.
        """
        self._impl.stop_scan()

    def toggle_torch(self, enabled: bool) -> None:
        """
        Toggles hardware flashlight/torch on supported devices.

        :param enabled: True to activate torch, False to deactivate.
        """
        self._impl.toggle_torch(enabled)

    def _inject_barcode(
        self,
        raw_value: str,
        format_: BarcodeFormat = BarcodeFormat.UPC_A,
        bounding_box: Optional[Tuple[float, float, float, float]] = None,
    ) -> None:
        """
        Synthetic injection helper forwarding to backend if supported, or directly dispatching.

        :param raw_value: Barcode string payload.
        :param format_: Symbology format.
        :param bounding_box: Optional bounding box coordinates.
        """
        if hasattr(self._impl, "_inject_barcode"):
            self._impl._inject_barcode(raw_value, format_, bounding_box)
        else:
            self._dispatch_barcode(raw_value, format_, bounding_box)

    def _dispatch_barcode(
        self,
        raw_value: str,
        format_: BarcodeFormat,
        bounding_box: Optional[Tuple[float, float, float, float]] = None,
    ) -> None:
        """
        Internal event dispatcher with debounce protection and format filtering.

        :param raw_value: Decoded barcode text.
        :param format_: Detected BarcodeFormat symbology.
        :param bounding_box: Optional normalized coordinates (x, y, w, h).
        """
        # Filter symbology formats if a restricted list was configured
        if BarcodeFormat.ALL not in self.formats and format_ not in self.formats:
            return

        now = time.time()
        # Debounce identical barcode scans received in rapid succession
        if (
            self._last_scanned_value == raw_value
            and (now - self._last_scan_time) * 1000 < self.debounce_ms
        ):
            return

        self._last_scan_time = now
        self._last_scanned_value = raw_value

        result = BarcodeResult(
            raw_value=raw_value,
            format=format_,
            bounding_box=bounding_box,
            timestamp=now,
        )

        if self.scan_mode == ScanMode.SINGLE_SHOT:
            self.stop_scan()

        if self.on_barcode:
            self.on_barcode(result)

    def _dispatch_error(self, message: str) -> None:
        """
        Internal error dispatcher routing error notifications to the `on_error` callback.

        :param message: Descriptive error message.
        """
        if self.on_error:
            self.on_error(message)
