"""
Unit tests for toga_barcode_scanner.android native Android backend.
"""

from unittest.mock import MagicMock, patch

import pytest

from toga_barcode_scanner import (
    BarcodeFormat,
    BarcodeResult,
    BarcodeScanner,
    CameraFacing,
    ScanMode,
)
from toga_barcode_scanner.android import (
    FORMAT_TO_MLKIT,
    MLKIT_FORMAT_QR_CODE,
    MLKIT_FORMAT_UPC_A,
    MLKIT_TO_FORMAT,
    AndroidBarcodeScanner,
    process_android_barcodes,
)


def test_android_format_mappings():
    assert FORMAT_TO_MLKIT[BarcodeFormat.QR_CODE] == MLKIT_FORMAT_QR_CODE
    assert FORMAT_TO_MLKIT[BarcodeFormat.UPC_A] == MLKIT_FORMAT_UPC_A
    assert MLKIT_TO_FORMAT[MLKIT_FORMAT_QR_CODE] == BarcodeFormat.QR_CODE
    assert MLKIT_TO_FORMAT[MLKIT_FORMAT_UPC_A] == BarcodeFormat.UPC_A


def test_android_process_barcodes_dispatch():
    scanned = []
    scanner = BarcodeScanner(
        on_barcode=lambda r: scanned.append(r),
        formats=[BarcodeFormat.QR_CODE],
        scan_mode=ScanMode.CONTINUOUS,
    )
    backend = AndroidBarcodeScanner(scanner)

    mock_barcode = MagicMock()
    mock_barcode.getRawValue.return_value = "https://sodatry.com/item/456"
    mock_barcode.getFormat.return_value = MLKIT_FORMAT_QR_CODE

    mock_rect = MagicMock()
    mock_rect.left = 10.0
    mock_rect.top = 20.0
    mock_rect.width.return_value = 100.0
    mock_rect.height.return_value = 200.0
    mock_barcode.getBoundingBox.return_value = mock_rect

    process_android_barcodes(backend, [mock_barcode])

    assert len(scanned) == 1
    assert scanned[0].raw_value == "https://sodatry.com/item/456"
    assert scanned[0].format == BarcodeFormat.QR_CODE
    assert scanned[0].bounding_box == (10.0, 20.0, 100.0, 200.0)


def test_android_permission_denied_start_scan():
    errors = []
    scanner = BarcodeScanner(
        on_error=lambda err: errors.append(err),
    )
    backend = AndroidBarcodeScanner(scanner)

    with patch.object(backend, "is_permission_granted", return_value=False):
        backend.start_scan()
        assert not backend.is_scanning
        assert len(errors) == 1
        assert errors[0] == "PERMISSION_DENIED"


def test_android_stop_scan_and_torch():
    scanner = BarcodeScanner()
    backend = AndroidBarcodeScanner(scanner)
    backend._is_scanning = True
    backend._torch_enabled = True

    mock_provider = MagicMock()
    backend._camera_provider = mock_provider

    backend.stop_scan()

    assert not backend.is_scanning
    assert not backend.is_torch_enabled
    assert mock_provider.unbindAll.called
