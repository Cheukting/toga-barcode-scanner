# toga-barcode-scanner 📷📦

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![BeeWare](https://img.shields.io/badge/BeeWare-Toga-orange.svg)](https://beeware.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A cross-platform, native camera barcode and QR code scanner hardware plugin for the **BeeWare** (`Toga`) ecosystem.

Offloads computer vision recognition to native operating system frameworks (**AVFoundation** on iOS, **CameraX + Google ML Kit** on Android) without blocking the Python GIL or UI rendering, providing instant scanning throughput with seamless mock fallbacks for desktop development.

---

## 🚀 Quick Start

### Installation

```bash
pip install toga-barcode-scanner
```

For iOS development environments:
```bash
pip install "toga-barcode-scanner[ios]"
```

### Usage Example

```python
import toga
from toga_barcode_scanner import BarcodeScanner, BarcodeFormat, BarcodeResult, ScanMode

class SodaTryMobileApp(toga.App):
    def startup(self):
        # 1. Initialize the scanner instance
        self.scanner = BarcodeScanner(
            app=self,
            on_barcode=self.handle_barcode,
            on_error=self.handle_error,
            formats=[BarcodeFormat.UPC_A, BarcodeFormat.EAN_13, BarcodeFormat.QR_CODE],
            scan_mode=ScanMode.SINGLE_SHOT,
            beep_on_scan=True,
            debounce_ms=300,
        )

        # 2. Add trigger button
        self.main_window = toga.MainWindow(title="Soda Catalog Scanner")
        self.main_window.content = toga.Button(
            "Scan Soda Barcode",
            on_press=lambda widget: self.scanner.start_scan(parent_window=self.main_window)
        )
        self.main_window.show()

    def handle_barcode(self, result: BarcodeResult):
        print(f"Scanned {result.format.value}: {result.raw_value}")
        # Process product lookup...
        self.main_window.info_dialog("Scan Result", f"Found barcode: {result.raw_value}")

    def handle_error(self, error_message: str):
        self.main_window.error_dialog("Camera Error", error_message)

def main():
    return SodaTryMobileApp("SodaTry", "com.sodatry.mobile")

if __name__ == "__main__":
    main().main_loop()
```

---

## 📱 Platform Support

| Platform | Underlying Engine | Direct Hardware Acceleration |
| :--- | :--- | :--- |
| **iOS** | `AVFoundation` + `UIKit` via `rubicon-objc` | ✅ Native Metal / Apple Neural Engine |
| **Android** | `CameraX` + Google `ML Kit Barcode Scanning` | ✅ Native GPU / Android NNAPI |
| **Desktop (macOS / Linux / Windows)** | Dummy Mock / Synthetic Event Injection | 🧪 Headless CI & Mock Dialogs |

---

## 🛠️ Briefcase Packaging Configuration

When packaging your BeeWare application using `briefcase`, configure target platform permissions and dependencies in `pyproject.toml`:

### iOS Configuration (`NSCameraUsageDescription`)

In your app's `pyproject.toml`:

```toml
[tool.briefcase.app.myapp.iOS]
info_plist_extra = { "NSCameraUsageDescription" = "Camera access is required to scan product barcodes." }
```

### Android Configuration (Permissions & Gradle Dependencies)

In your app's `pyproject.toml`:

```toml
[tool.briefcase.app.myapp.android]
permissions = [
    "android.permission.CAMERA",
]
features = [
    "android.hardware.camera",
]
build_gradle_dependencies = [
    "androidx.camera:camera-core:1.3.1",
    "androidx.camera:camera-camera2:1.3.1",
    "androidx.camera:camera-lifecycle:1.3.1",
    "androidx.camera:camera-view:1.3.1",
    "com.google.mlkit:barcode-scanning:17.2.0",
]
```

---

## 🧪 Testing & Synthetic Event Injection

The dummy backend allows programmatic simulation of barcode events for headless CI and desktop testing without physical cameras:

```python
from toga_barcode_scanner import BarcodeScanner, BarcodeFormat

scanner = BarcodeScanner(
    on_barcode=lambda res: print(f"Received {res.raw_value}"),
    backend="dummy",
)

scanner.start_scan()
# Programmatically inject a barcode scan event
scanner._inject_barcode("012000000133", BarcodeFormat.UPC_A)
```

---

## 📖 Documentation

* [Technical Architecture & Design Specification (DESIGN.md)](DESIGN.md)
* [Milestones & Development Plan (PLAN.md)](PLAN.md)
* [Contribution Guidelines (CONTRIBUTING.md)](CONTRIBUTING.md)
* [Release History (CHANGELOG.md)](CHANGELOG.md)

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for details.
