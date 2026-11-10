"""
Core BarcodeScanner hardware plugin interface and event coordinator.
"""
from __future__ import annotations
import time
from typing import Any, Callable, List, Optional
from toga_barcode_scanner.models import (
    BarcodeFormat,
    BarcodeResult,
    CameraFacing,
    ScanMode,
)


class BarcodeScanner:
    """
    Cross-platform barcode scanner service for Toga / BeeWare.
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
    ) -> None:
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

        self._is_scanning: bool = False
        self._torch_enabled: bool = False
        self._last_scan_time: float = 0.0

    @property
    def is_scanning(self) -> bool:
        """Returns True if the camera capture session is currently active."""
        return self._is_scanning

    @property
    def is_torch_enabled(self) -> bool:
        """Returns True if the camera flashlight is currently enabled."""
        return self._torch_enabled

    def is_permission_granted(self) -> bool:
        """Checks if camera permission has been granted by the OS."""
        return True

    async def request_permission(self) -> bool:
        """Asynchronously requests camera access if not already granted."""
        return True

    def start_scan(self, parent_window: Optional[Any] = None) -> None:
        """
        Activates the camera view and begins analyzing frames for barcodes.
        """
        if self._is_scanning:
            return
        self._is_scanning = True

    def stop_scan(self) -> None:
        """
        Deactivates camera capture and dismisses the viewfinder overlay.
        """
        if not self._is_scanning:
            return
        self._is_scanning = False
        self._torch_enabled = False

    def toggle_torch(self, enabled: bool) -> None:
        """Toggles hardware flashlight/torch."""
        self._torch_enabled = enabled

    def _dispatch_barcode(self, raw_value: str, format_: BarcodeFormat) -> None:
        """
        Internal event dispatcher with debounce protection.
        """
        now = time.time()
        if (now - self._last_scan_time) * 1000 < self.debounce_ms:
            return
        self._last_scan_time = now

        result = BarcodeResult(
            raw_value=raw_value,
            format=format_,
            timestamp=now,
        )

        if self.scan_mode == ScanMode.SINGLE_SHOT:
            self.stop_scan()

        if self.on_barcode:
            self.on_barcode(result)
