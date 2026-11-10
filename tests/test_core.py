"""
Unit tests for toga_barcode_scanner core interface and models.
"""
import pytest
from toga_barcode_scanner import (
    BarcodeFormat,
    BarcodeResult,
    BarcodeScanner,
    CameraFacing,
    ScanMode,
)


def test_models_initialization():
    result = BarcodeResult(
        raw_value="012000000133",
        format=BarcodeFormat.UPC_A,
        bounding_box=(0.1, 0.2, 0.8, 0.6),
        timestamp=1700000000.0,
    )
    assert result.raw_value == "012000000133"
    assert result.format == BarcodeFormat.UPC_A
    assert result.bounding_box == (0.1, 0.2, 0.8, 0.6)
    assert result.timestamp == 1700000000.0


def test_scanner_lifecycle():
    scanned_results = []

    def on_barcode(res: BarcodeResult):
        scanned_results.append(res)

    scanner = BarcodeScanner(
        on_barcode=on_barcode,
        formats=[BarcodeFormat.UPC_A, BarcodeFormat.EAN_13],
        scan_mode=ScanMode.SINGLE_SHOT,
    )

    assert not scanner.is_scanning
    assert not scanner.is_torch_enabled

    scanner.start_scan()
    assert scanner.is_scanning

    scanner.toggle_torch(True)
    assert scanner.is_torch_enabled

    # Simulate hardware barcode detection event
    scanner._dispatch_barcode("012000000133", BarcodeFormat.UPC_A)

    assert len(scanned_results) == 1
    assert scanned_results[0].raw_value == "012000000133"
    assert scanned_results[0].format == BarcodeFormat.UPC_A
    # Single-shot mode should automatically stop scanning
    assert not scanner.is_scanning


def test_scanner_debounce():
    scanned = []
    scanner = BarcodeScanner(
        on_barcode=lambda r: scanned.append(r),
        debounce_ms=500,
        scan_mode=ScanMode.CONTINUOUS,
    )

    scanner.start_scan()
    scanner._dispatch_barcode("123456789012", BarcodeFormat.EAN_13)
    # Immediate repeat scan should be debounced
    scanner._dispatch_barcode("123456789012", BarcodeFormat.EAN_13)

    assert len(scanned) == 1
    scanner.stop_scan()
    assert not scanner.is_scanning
