"""
Data models and enumerations for toga-barcode-scanner.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple


class BarcodeFormat(Enum):
    """Supported 1D and 2D barcode symbologies."""
    UPC_A = "upc_a"
    UPC_E = "upc_e"
    EAN_8 = "ean_8"
    EAN_13 = "ean_13"
    CODE_39 = "code_39"
    CODE_128 = "code_128"
    QR_CODE = "qr_code"
    DATA_MATRIX = "data_matrix"
    AZTEC = "aztec"
    ALL = "all"


class CameraFacing(Enum):
    """Hardware camera sensor direction."""
    BACK = "back"
    FRONT = "front"


class ScanMode(Enum):
    """Operation mode for barcode capture."""
    CONTINUOUS = "continuous"    # Continuously streams detections until stopped
    SINGLE_SHOT = "single_shot"  # Automatically stops after first valid barcode


@dataclass(frozen=True)
class BarcodeResult:
    """Immutable result representing a decoded barcode scan event."""
    raw_value: str
    format: BarcodeFormat
    bounding_box: Optional[Tuple[float, float, float, float]] = None
    timestamp: float = 0.0
