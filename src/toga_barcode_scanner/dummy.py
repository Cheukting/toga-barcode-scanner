"""
Dummy / Mock backend implementation for toga-barcode-scanner.

This backend provides desktop and headless CI fallbacks, enabling unit testing,
synthetic event injection, and desktop UI simulation without physical camera hardware.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Tuple

from toga_barcode_scanner.factory import BaseBarcodeScannerBackend
from toga_barcode_scanner.models import BarcodeFormat

if TYPE_CHECKING:
    from toga_barcode_scanner.core import BarcodeScanner


class DummyBarcodeScanner(BaseBarcodeScannerBackend):
    """
    Simulated barcode scanner backend for testing and desktop development.

    Supports programmatic event injection (`_inject_barcode`), error simulation (`_inject_error`),
    and configurable permission states for deterministic testing in headless environments.
    """

    def __init__(self, interface: BarcodeScanner) -> None:
        """
        Initialize the dummy backend instance.

        :param interface: The coordinating BarcodeScanner instance.
        """
        super().__init__(interface)
        self._permission_granted: bool = True
        self._parent_window: Optional[Any] = None
        self._injected_events_count: int = 0

    def is_permission_granted(self) -> bool:
        """
        Return the configured mock camera permission state.

        :return: True if authorized, False otherwise.
        """
        return self._permission_granted

    def set_permission_granted(self, granted: bool) -> None:
        """
        Configure the simulated camera permission state for unit testing.

        :param granted: Boolean indicating if permission should be granted.
        """
        self._permission_granted = granted

    async def request_permission(self) -> bool:
        """
        Simulate an asynchronous OS camera permission request dialog.

        :return: The mock permission state.
        """
        return self._permission_granted

    def start_scan(self, parent_window: Optional[Any] = None) -> None:
        """
        Simulate activating the camera viewfinder.

        If permissions are denied, an error is dispatched to the core coordinator
        and scanning remains inactive.

        :param parent_window: Optional parent Toga window.
        """
        if not self._permission_granted:
            self.interface._dispatch_error("PERMISSION_DENIED")
            return

        self._parent_window = parent_window
        self._is_scanning = True

    def stop_scan(self) -> None:
        """
        Deactivate simulated scanning session and reset torch state.
        """
        self._is_scanning = False
        self._torch_enabled = False

    def toggle_torch(self, enabled: bool) -> None:
        """
        Toggle mock hardware torch state.

        :param enabled: True to turn on torch, False to turn off.
        """
        self._torch_enabled = enabled

    def _inject_barcode(
        self,
        raw_value: str,
        format_: BarcodeFormat = BarcodeFormat.UPC_A,
        bounding_box: Optional[Tuple[float, float, float, float]] = None,
    ) -> None:
        """
        Synthetically inject a barcode detection event into the coordinator.

        This method facilitates deterministic testing in CI pipelines and unit tests
        without requiring physical camera sensors or physical barcode labels.

        :param raw_value: The decoded string data of the barcode.
        :param format_: The BarcodeFormat symbology (defaults to UPC_A).
        :param bounding_box: Optional normalized bounding box tuple (x, y, w, h).
        """
        if not self._is_scanning:
            return

        self._injected_events_count += 1
        self.interface._dispatch_barcode(raw_value, format_, bounding_box)

    def _inject_error(self, message: str) -> None:
        """
        Synthetically dispatch an error message to the core coordinator.

        :param message: Descriptive error string to dispatch.
        """
        self.interface._dispatch_error(message)
