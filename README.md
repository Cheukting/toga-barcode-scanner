# toga-barcode-scanner 📷📦

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![BeeWare](https://img.shields.io/badge/BeeWare-Toga-orange.svg)](https://beeware.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A cross-platform, native camera barcode and QR code scanner plugin for the **BeeWare** (`Toga`) ecosystem.

Built to provide seamless, zero-lag UPC/EAN barcode scanning on **iOS** (`AVFoundation` via `rubicon-objc`) and **Android** (`CameraX` & Google `ML Kit`), with desktop/simulator fallback support for development and headless CI pipelines.

---

## 🚀 Quick Start

### Installation

```bash
pip install toga-barcode-scanner
```

### Usage Example

```python
import toga
from toga_barcode_scanner import BarcodeScanner, BarcodeFormat, BarcodeResult

class ExampleApp(toga.App):
    def startup(self):
        # 1. Initialize the scanner instance
        self.scanner = BarcodeScanner(
            app=self,
            on_barcode=self.handle_barcode,
            formats=[BarcodeFormat.UPC_A, BarcodeFormat.EAN_13, BarcodeFormat.QR_CODE],
            beep_on_scan=True
        )

        # 2. Add trigger button
        self.main_window = toga.MainWindow(title="Barcode Scanner Demo")
        self.main_window.content = toga.Button(
            "Scan Barcode",
            on_press=lambda widget: self.scanner.start_scan(parent_window=self.main_window)
        )
        self.main_window.show()

    def handle_barcode(self, result: BarcodeResult):
        print(f"Scanned {result.format.value}: {result.raw_value}")
        self.scanner.stop_scan()
        self.main_window.info_dialog("Scan Complete", f"Barcode: {result.raw_value}")

def main():
    return ExampleApp("Barcode Demo", "org.beeware.barcodedemo")

if __name__ == "__main__":
    main().main_loop()
```

---

## 📱 Platform Support

| Platform | Underlying Engine | Direct Hardware Acceleration |
| :--- | :--- | :--- |
| **iOS** | `AVFoundation` + `Vision` via `rubicon-objc` | ✅ Native Metal / Neural Engine |
| **Android** | `CameraX` + Google `ML Kit Barcode Scanning` | ✅ Native GPU / NNAPI |
| **Desktop (macOS/Linux/Windows)** | Dummy Mock / File Upload / Synthetic Injection | 🧪 Mock Test Mode |

---

## 📖 Documentation

* [Technical Architecture & Design Specification (DESIGN.md)](DESIGN.md)
* [Milestones & Development Plan (PLAN.md)](PLAN.md)
* [Contribution Guidelines (CONTRIBUTING.md)](CONTRIBUTING.md)
* [Release History (CHANGELOG.md)](CHANGELOG.md)

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for details.
