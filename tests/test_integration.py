"""
Integration tests validating toga-barcode-scanner workflows in application contexts (e.g., SodaTry).
"""

import pytest

from toga_barcode_scanner import (
    BarcodeFormat,
    BarcodeResult,
    BarcodeScanner,
    CameraFacing,
    ScanMode,
)


class MockSodaCatalogService:
    """Mock backend service simulating catalog queries by UPC barcode."""

    def __init__(self):
        self.catalog = {
            "012000000133": {"brand": "Pepsi", "flavor": "Cola", "size_oz": 12},
            "049000000443": {"brand": "Coca-Cola", "flavor": "Classic", "size_oz": 12},
            "078000082463": {"brand": "Dr Pepper", "flavor": "Regular", "size_oz": 12},
        }
        self.queried_items = []

    def lookup_soda(self, upc: str):
        item = self.catalog.get(upc)
        if item:
            self.queried_items.append(item)
        return item


def test_sodatry_single_shot_catalog_scan():
    """Validate full flow of scanning a single soda can and fetching product details."""
    catalog = MockSodaCatalogService()
    scanned_sodas = []

    def on_barcode_scanned(result: BarcodeResult):
        product = catalog.lookup_soda(result.raw_value)
        if product:
            scanned_sodas.append(product)

    scanner = BarcodeScanner(
        on_barcode=on_barcode_scanned,
        formats=[BarcodeFormat.UPC_A, BarcodeFormat.EAN_13],
        scan_mode=ScanMode.SINGLE_SHOT,
        backend="dummy",
    )

    # 1. Start scan flow
    scanner.start_scan()
    assert scanner.is_scanning

    # 2. Simulate user pointing camera at a Dr Pepper can
    scanner._inject_barcode("078000082463", BarcodeFormat.UPC_A)

    # 3. Scanner should auto-dismiss on first valid read in SINGLE_SHOT mode
    assert not scanner.is_scanning
    assert len(scanned_sodas) == 1
    assert scanned_sodas[0]["brand"] == "Dr Pepper"
    assert scanned_sodas[0]["flavor"] == "Regular"


def test_sodatry_continuous_inventory_tasting_scan():
    """Validate continuous batch scanning across multiple distinct cans with debouncing."""
    catalog = MockSodaCatalogService()
    scanned_sodas = []

    def on_barcode_scanned(result: BarcodeResult):
        product = catalog.lookup_soda(result.raw_value)
        if product:
            scanned_sodas.append(product)

    scanner = BarcodeScanner(
        on_barcode=on_barcode_scanned,
        formats=[BarcodeFormat.UPC_A],
        scan_mode=ScanMode.CONTINUOUS,
        debounce_ms=200,
        backend="dummy",
    )

    scanner.start_scan()
    assert scanner.is_scanning

    # Scan Pepsi can (multiple frames of same can)
    scanner._inject_barcode("012000000133", BarcodeFormat.UPC_A)
    scanner._inject_barcode("012000000133", BarcodeFormat.UPC_A)
    assert len(scanned_sodas) == 1
    assert scanned_sodas[0]["brand"] == "Pepsi"

    # Scan Coca-Cola can
    scanner._inject_barcode("049000000443", BarcodeFormat.UPC_A)
    assert len(scanned_sodas) == 2
    assert scanned_sodas[1]["brand"] == "Coca-Cola"

    # Toggle flashlight while scanning remains active
    scanner.toggle_torch(True)
    assert scanner.is_torch_enabled
    assert scanner.is_scanning

    # Stop continuous inventory capture
    scanner.stop_scan()
    assert not scanner.is_scanning
    assert not scanner.is_torch_enabled
