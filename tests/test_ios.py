"""
Unit tests for toga_barcode_scanner.ios native iOS backend.
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
from toga_barcode_scanner.ios import (
    AV_METADATA_TO_FORMAT,
    FORMAT_TO_AV_METADATA,
    HAS_RUBICON_OBJC,
    AVAuthorizationStatusAuthorized,
    AVAuthorizationStatusDenied,
    BarcodeCaptureDelegate,
    iOSBarcodeScanner,
    process_ios_metadata_objects,
)


def test_ios_format_mappings():
    assert FORMAT_TO_AV_METADATA[BarcodeFormat.QR_CODE] == "org.iso.QRCode"
    assert FORMAT_TO_AV_METADATA[BarcodeFormat.EAN_13] == "org.gs1.EAN-13"
    assert FORMAT_TO_AV_METADATA[BarcodeFormat.UPC_E] == "org.gs1.UPC-E"
    assert AV_METADATA_TO_FORMAT["org.iso.QRCode"] == BarcodeFormat.QR_CODE
    assert AV_METADATA_TO_FORMAT["org.gs1.EAN-13"] == BarcodeFormat.EAN_13


def test_ios_metadata_processing_dispatch():
    scanned = []
    scanner = BarcodeScanner(
        on_barcode=lambda r: scanned.append(r),
        formats=[BarcodeFormat.QR_CODE],
        scan_mode=ScanMode.CONTINUOUS,
    )
    backend = iOSBarcodeScanner(scanner)

    # Create mock metadata object
    mock_obj = MagicMock()
    mock_obj.stringValue = "https://sodatry.com/item/123"
    mock_obj.type = "org.iso.QRCode"

    mock_bounds = MagicMock()
    mock_bounds.origin.x = 0.1
    mock_bounds.origin.y = 0.2
    mock_bounds.size.width = 0.5
    mock_bounds.size.height = 0.6
    mock_obj.bounds = mock_bounds

    mock_array = MagicMock()
    mock_array.count = 1
    mock_array.objectAtIndex_.return_value = mock_obj

    process_ios_metadata_objects(backend, mock_array)

    assert len(scanned) == 1
    assert scanned[0].raw_value == "https://sodatry.com/item/123"
    assert scanned[0].format == BarcodeFormat.QR_CODE
    assert scanned[0].bounding_box == (0.1, 0.2, 0.5, 0.6)


def test_ios_metadata_upca_normalization():
    scanned = []
    scanner = BarcodeScanner(
        on_barcode=lambda r: scanned.append(r),
        formats=[BarcodeFormat.UPC_A],
        scan_mode=ScanMode.CONTINUOUS,
    )
    backend = iOSBarcodeScanner(scanner)

    # In AVFoundation, UPC-A is reported as 13-digit EAN-13 starting with 0
    mock_obj = MagicMock()
    mock_obj.stringValue = "0012000000133"
    mock_obj.type = "org.gs1.EAN-13"
    mock_obj.bounds = None

    mock_array = MagicMock()
    mock_array.count = 1
    mock_array.objectAtIndex_.return_value = mock_obj

    process_ios_metadata_objects(backend, mock_array)

    assert len(scanned) == 1
    assert scanned[0].raw_value == "012000000133"
    assert scanned[0].format == BarcodeFormat.UPC_A


def test_ios_target_metadata_types_resolution():
    scanner = BarcodeScanner(formats=[BarcodeFormat.UPC_E, BarcodeFormat.QR_CODE])
    backend = iOSBarcodeScanner(scanner)
    target_types = backend._get_target_metadata_types()
    assert "org.gs1.UPC-E" in target_types
    assert "org.iso.QRCode" in target_types
    assert "org.iso.Aztec" not in target_types


def test_ios_permission_denied_start_scan():
    errors = []
    scanner = BarcodeScanner(
        on_error=lambda err: errors.append(err),
    )
    backend = iOSBarcodeScanner(scanner)

    with patch.object(backend, "is_permission_granted", return_value=False):
        backend.start_scan()
        assert not backend.is_scanning
        assert len(errors) == 1
        assert errors[0] == "PERMISSION_DENIED"


def test_ios_stop_scan_and_torch():
    scanner = BarcodeScanner()
    backend = iOSBarcodeScanner(scanner)
    backend._is_scanning = True
    backend._torch_enabled = True

    mock_session = MagicMock()
    mock_session.isRunning = True
    backend._session = mock_session

    backend.stop_scan()

    assert not backend.is_scanning
    assert not backend.is_torch_enabled
    assert mock_session.stopRunning.called
