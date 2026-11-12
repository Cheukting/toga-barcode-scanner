"""
toga-barcode-scanner: Cross-platform native barcode scanner for BeeWare / Toga.
"""

from toga_barcode_scanner.android import AndroidBarcodeScanner
from toga_barcode_scanner.core import BarcodeScanner
from toga_barcode_scanner.dummy import DummyBarcodeScanner
from toga_barcode_scanner.factory import (
    BaseBarcodeScannerBackend,
    get_platform_scanner,
)
from toga_barcode_scanner.ios import iOSBarcodeScanner
from toga_barcode_scanner.models import (
    BarcodeFormat,
    BarcodeResult,
    CameraFacing,
    ScanMode,
)

__version__ = "0.1.2"

__all__ = [
    "BarcodeScanner",
    "BarcodeFormat",
    "BarcodeResult",
    "CameraFacing",
    "ScanMode",
    "BaseBarcodeScannerBackend",
    "DummyBarcodeScanner",
    "iOSBarcodeScanner",
    "AndroidBarcodeScanner",
    "get_platform_scanner",
]
