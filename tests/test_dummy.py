"""
Unit tests for toga_barcode_scanner.dummy backend service.
"""

import pytest

from toga_barcode_scanner import (
    BarcodeFormat,
    BarcodeResult,
    BarcodeScanner,
    DummyBarcodeScanner,
    ScanMode,
)


def test_dummy_backend_lifecycle():
    scanned = []
    scanner = BarcodeScanner(
        on_barcode=lambda r: scanned.append(r),
        backend="dummy",
    )
    dummy = scanner._impl
    assert isinstance(dummy, DummyBarcodeScanner)

    assert not dummy.is_scanning
    assert not dummy.is_torch_enabled
    assert dummy.is_permission_granted()

    dummy.start_scan()
    assert dummy.is_scanning

    dummy.toggle_torch(True)
    assert dummy.is_torch_enabled

    dummy.toggle_torch(False)
    assert not dummy.is_torch_enabled

    dummy.stop_scan()
    assert not dummy.is_scanning


@pytest.mark.asyncio
async def test_dummy_permission_controls():
    errors = []
    scanner = BarcodeScanner(
        on_error=lambda err: errors.append(err),
        backend="dummy",
    )
    dummy: DummyBarcodeScanner = scanner._impl

    assert dummy.is_permission_granted()
    assert await dummy.request_permission() is True

    # Simulate permission denial
    dummy.set_permission_granted(False)
    assert not dummy.is_permission_granted()
    assert await dummy.request_permission() is False

    # Attempting to start scan with denied permission should dispatch error
    dummy.start_scan()
    assert not dummy.is_scanning
    assert len(errors) == 1
    assert errors[0] == "PERMISSION_DENIED"


def test_dummy_synthetic_event_injection():
    scanned = []
    scanner = BarcodeScanner(
        on_barcode=lambda r: scanned.append(r),
        scan_mode=ScanMode.CONTINUOUS,
        backend="dummy",
    )
    dummy: DummyBarcodeScanner = scanner._impl

    # Injections when not scanning should be ignored
    dummy._inject_barcode("012000000133", BarcodeFormat.UPC_A)
    assert len(scanned) == 0

    dummy.start_scan()
    dummy._inject_barcode(
        "012000000133",
        BarcodeFormat.UPC_A,
        bounding_box=(0.1, 0.1, 0.8, 0.8),
    )

    assert len(scanned) == 1
    assert scanned[0].raw_value == "012000000133"
    assert scanned[0].format == BarcodeFormat.UPC_A
    assert scanned[0].bounding_box == (0.1, 0.1, 0.8, 0.8)
    assert dummy._injected_events_count == 1


def test_dummy_inject_error():
    errors = []
    scanner = BarcodeScanner(
        on_error=lambda err: errors.append(err),
        backend="dummy",
    )
    dummy: DummyBarcodeScanner = scanner._impl

    dummy._inject_error("CAMERA_UNAVAILABLE")
    assert len(errors) == 1
    assert errors[0] == "CAMERA_UNAVAILABLE"
