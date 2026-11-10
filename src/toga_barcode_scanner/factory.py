"""
Backend factory and base interface contract for toga-barcode-scanner.

This module defines the abstract base backend class `BaseBarcodeScannerBackend`
and the factory function `get_platform_scanner` that resolves and instantiates
the appropriate platform-specific implementation (iOS, Android, or Dummy)
at runtime.
"""

from __future__ import annotations

import abc
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from toga_barcode_scanner.core import BarcodeScanner


class BaseBarcodeScannerBackend(abc.ABC):
    """
    Abstract base class establishing the contract for platform scanner backends.

    Each concrete backend (iOS, Android, Dummy) implements camera session lifecycle,
    permission queries, torch toggling, and event forwarding back to the
    `BarcodeScanner` core coordinator interface.
    """

    def __init__(self, interface: BarcodeScanner) -> None:
        """
        Initialize the backend with a reference to the public `BarcodeScanner` interface.

        :param interface: The coordinating BarcodeScanner instance.
        """
        self.interface = interface
        self._is_scanning: bool = False
        self._torch_enabled: bool = False

    @property
    def is_scanning(self) -> bool:
        """Returns True if the backend capture session is currently active."""
        return self._is_scanning

    @property
    def is_torch_enabled(self) -> bool:
        """Returns True if the device hardware flashlight/torch is enabled."""
        return self._torch_enabled

    @abc.abstractmethod
    def is_permission_granted(self) -> bool:
        """
        Check if the host operating system has granted camera capture permission.

        :return: True if authorized, False otherwise.
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def request_permission(self) -> bool:
        """
        Asynchronously prompt the user for camera access permissions if not already granted.

        :return: True if access is authorized, False if denied.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def start_scan(self, parent_window: Optional[Any] = None) -> None:
        """
        Activate the camera capture pipeline and present the viewfinder overlay.

        :param parent_window: Optional parent Toga window used for modal presentation.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def stop_scan(self) -> None:
        """
        Deactivate camera stream, dismiss the viewfinder, and release camera resources.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def toggle_torch(self, enabled: bool) -> None:
        """
        Enable or disable the hardware flashlight/torch.

        :param enabled: True to turn on torch, False to turn off.
        """
        raise NotImplementedError


def get_platform_scanner(
    interface: BarcodeScanner,
    backend: Optional[str | BaseBarcodeScannerBackend] = None,
) -> BaseBarcodeScannerBackend:
    """
    Resolve and instantiate the appropriate scanner backend for the active runtime platform.

    Resolution strategy:
    1. Explicit backend instance: returned directly.
    2. Explicit backend string ('ios', 'android', 'dummy'): loads matching backend.
    3. Auto-detection via `toga.platform.current_platform`:
       - 'iOS' -> `toga_barcode_scanner.ios.iOSBarcodeScanner`
       - 'android' -> `toga_barcode_scanner.android.AndroidBarcodeScanner`
       - Desktop/Fallback -> `toga_barcode_scanner.dummy.DummyBarcodeScanner`

    :param interface: The core `BarcodeScanner` instance requiring a backend.
    :param backend: Optional explicit backend override.
    :return: An initialized instance of `BaseBarcodeScannerBackend`.
    """
    if isinstance(backend, BaseBarcodeScannerBackend):
        return backend

    target = backend
    if target is None:
        try:
            import toga.platform

            target = toga.platform.current_platform
        except Exception:
            target = "dummy"

    target_normalized = str(target).lower() if target else "dummy"

    if target_normalized in ("ios", "iphone", "ipad"):
        try:
            from toga_barcode_scanner.ios import iOSBarcodeScanner  # type: ignore[import-not-found,import-untyped]  # isort: skip

            return iOSBarcodeScanner(interface)
        except ImportError:
            # If native iOS dependencies (rubicon-objc) are unavailable, fallback to Dummy
            from toga_barcode_scanner.dummy import DummyBarcodeScanner

            return DummyBarcodeScanner(interface)

    elif target_normalized in ("android",):
        try:
            from toga_barcode_scanner.android import AndroidBarcodeScanner  # type: ignore[import-not-found,import-untyped]  # isort: skip

            return AndroidBarcodeScanner(interface)
        except ImportError:
            # If native Android dependencies are unavailable, fallback to Dummy
            from toga_barcode_scanner.dummy import DummyBarcodeScanner

            return DummyBarcodeScanner(interface)

    else:
        from toga_barcode_scanner.dummy import DummyBarcodeScanner

        return DummyBarcodeScanner(interface)
