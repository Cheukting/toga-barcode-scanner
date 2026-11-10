"""
Unit tests for toga_barcode_scanner.factory backend resolution.
"""

import sys
from unittest.mock import MagicMock, patch

import pytest

from toga_barcode_scanner import (
    BarcodeScanner,
    BaseBarcodeScannerBackend,
    DummyBarcodeScanner,
    get_platform_scanner,
)
from toga_barcode_scanner.android import AndroidBarcodeScanner
from toga_barcode_scanner.ios import iOSBarcodeScanner


def test_factory_resolves_dummy_by_default():
    scanner = BarcodeScanner()
    assert isinstance(scanner._impl, DummyBarcodeScanner)


def test_factory_resolves_explicit_dummy_string():
    scanner = BarcodeScanner(backend="dummy")
    assert isinstance(scanner._impl, DummyBarcodeScanner)


def test_factory_resolves_ios():
    scanner = BarcodeScanner(backend="dummy")
    backend = get_platform_scanner(scanner, backend="ios")
    assert isinstance(backend, iOSBarcodeScanner)


def test_factory_resolves_android():
    scanner = BarcodeScanner(backend="dummy")
    backend = get_platform_scanner(scanner, backend="android")
    assert isinstance(backend, AndroidBarcodeScanner)


def test_factory_accepts_custom_backend_instance():
    class CustomBackend(BaseBarcodeScannerBackend):
        def is_permission_granted(self) -> bool:
            return True

        async def request_permission(self) -> bool:
            return True

        def start_scan(self, parent_window=None) -> None:
            self._is_scanning = True

        def stop_scan(self) -> None:
            self._is_scanning = False

        def toggle_torch(self, enabled: bool) -> None:
            self._torch_enabled = enabled

    dummy_core = BarcodeScanner(backend="dummy")
    custom_backend = CustomBackend(dummy_core)
    scanner = BarcodeScanner(backend=custom_backend)
    assert scanner._impl is custom_backend


def test_factory_ios_import_fallback():
    scanner = BarcodeScanner(backend="dummy")
    with patch.dict(sys.modules, {"toga_barcode_scanner.ios": None}):
        backend = get_platform_scanner(scanner, backend="ios")
        assert isinstance(backend, DummyBarcodeScanner)


def test_factory_android_import_fallback():
    scanner = BarcodeScanner(backend="dummy")
    with patch.dict(sys.modules, {"toga_barcode_scanner.android": None}):
        backend = get_platform_scanner(scanner, backend="android")
        assert isinstance(backend, DummyBarcodeScanner)


def test_factory_auto_detect_platform_fallback():
    mock_toga = MagicMock()
    mock_toga.platform.current_platform = "macOS"

    with patch.dict(
        sys.modules, {"toga": mock_toga, "toga.platform": mock_toga.platform}
    ):
        scanner = BarcodeScanner(backend="dummy")
        backend = get_platform_scanner(scanner)
        assert isinstance(backend, DummyBarcodeScanner)
