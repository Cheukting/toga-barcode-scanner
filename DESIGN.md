# Technical Design Document: Toga Barcode Scanner Plugin (`toga-barcode-scanner`)

## 1. Executive Summary

`toga-barcode-scanner` is a Python-native hardware plugin for the **BeeWare** ecosystem (specifically **Toga**) that provides cross-platform camera-based barcode and QR code scanning capabilities on **iOS** and **Android**, with mock/fallback support for desktop environments (`macOS`, `Linux`, `Windows`).

The primary motivation is enabling real-time UPC/EAN barcode scanning for mobile applications built with BeeWare (such as the **SodaTry** beverage discovery platform) without requiring developers to leave the Python ecosystem or write custom native Objective-C/Swift/Java bridges for their application layer.

---

## 2. Design Goals & Principles

1. **Idiomatic Python & Toga API**: Expose a clean, asynchronous Python interface following Toga widget and hardware service conventions.
2. **Zero-Lag Hardware Execution**: Camera frame ingestion, hardware acceleration, and computer vision recognition must execute on native OS threads (`AVFoundation` / `CameraX` + `ML Kit`) to prevent blocking the Python GIL or UI rendering.
3. **Decoupled Architecture**: Follow Toga's core/backend separation pattern (`toga_barcode_scanner.core` vs. `toga_barcode_scanner.ios`, `toga_barcode_scanner.android`, `toga_barcode_scanner.dummy`).
4. **Batteries-Included Permission & Overlay Management**: Handle camera authorization workflows, visual viewfinder overlays, target reticles, torch/flashlight toggles, and tap-to-focus natively.
5. **Broad Symbology Support**: Support standard retail 1D barcodes (UPC-A, UPC-E, EAN-8, EAN-13, Code 39, Code 128) and 2D formats (QR Code, Data Matrix, Aztec).

---

## 3. High-Level System Architecture

```
+-------------------------------------------------------------------------+
|                       Application Layer (e.g. SodaTry)                  |
|                     Imports `toga_barcode_scanner`                      |
+-------------------------------------------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
|                 `toga_barcode_scanner.core.BarcodeScanner`              |
|        - Public API: `start_scan()`, `stop_scan()`, `toggle_torch()`   |
|        - Event routing: `on_barcode`, `on_error`, `on_permission_denied`|
|        - Configuration: `symbologies`, `scan_mode`, `camera_facing`     |
+-------------------------------------------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
|                  Factory Backend Resolution / Interface                 |
|             (`toga_barcode_scanner.factory.get_platform_scanner()`)     |
+-------------------------------------------------------------------------+
          /                                 |                           \
         v                                  v                            v
+------------------------+      +------------------------+      +------------------------+
|      iOS Backend       |      |    Android Backend     |      |     Dummy / Mock       |
|    (`rubicon-objc`)    |      |    (Chaquopy / IPC)    |      |      (Desktop / CI)    |
| - `AVCaptureSession`   |      | - `CameraX` / Preview  |      | - Mock file/webcam     |
| - `AVCaptureMetadata`  |      | - Google `ML Kit`      |      | - Synthetic barcode    |
| - `Vision` Framework   |      | - Lifecycle & Manifest |      |   event injection      |
+------------------------+      +------------------------+      +------------------------+
```

---

## 4. Detailed Component Design

### 4.1. Core API Layer (`toga_barcode_scanner.core`)

#### Data Models (`toga_barcode_scanner.models`)
```python
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple

class BarcodeFormat(Enum):
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
    BACK = "back"
    FRONT = "front"

class ScanMode(Enum):
    CONTINUOUS = "continuous"    # Keeps scanning until explicitly stopped
    SINGLE_SHOT = "single_shot"  # Auto-stops and closes after first successful read

@dataclass(frozen=True)
class BarcodeResult:
    raw_value: str
    format: BarcodeFormat
    bounding_box: Optional[Tuple[float, float, float, float]] = None  # (x, y, width, height) in normalized (0.0-1.0) coordinates
    timestamp: float = 0.0
```

#### Public Class Interface (`toga_barcode_scanner.BarcodeScanner`)
```python
class BarcodeScanner:
    def __init__(
        self,
        app: toga.App,
        on_barcode: Optional[Callable[[BarcodeResult], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
        formats: List[BarcodeFormat] = [BarcodeFormat.ALL],
        camera_facing: CameraFacing = CameraFacing.BACK,
        scan_mode: ScanMode = ScanMode.SINGLE_SHOT,
        show_overlay: bool = True,
        beep_on_scan: bool = True,
        vibrate_on_scan: bool = True,
    ): ...

    async def request_permission(self) -> bool:
        """Asynchronously requests camera access if not already granted."""
        ...

    def is_permission_granted(self) -> bool:
        """Returns True if camera permission is authorized."""
        ...

    def start_scan(self, parent_window: Optional[toga.Window] = None) -> None:
        """Launches camera capture view / modal overlay."""
        ...

    def stop_scan(self) -> None:
        """Stops video stream and dismisses scanner view."""
        ...

    def toggle_torch(self, enabled: bool) -> None:
        """Toggles hardware flashlight on supported devices."""
        ...

    @property
    def is_scanning(self) -> bool: ...
```

---

## 5. Platform-Specific Native Implementations

### 5.1. iOS Backend (`toga_barcode_scanner.ios`)

The iOS implementation relies on Apple's zero-dependency built-in `AVFoundation` and `CoreMedia` frameworks via **`rubicon-objc`**.

#### Architecture:
1. **Camera Session Setup**:
   * Creates an `AVCaptureSession` configured with preset `AVCaptureSessionPresetHigh`.
   * Acquires the default back-facing `AVCaptureDevice` (wide-angle camera).
   * Attaches an `AVCaptureDeviceInput` to the session.
2. **Metadata Processing**:
   * Creates an `AVCaptureMetadataOutput` instance and adds it to the session.
   * Maps Python `BarcodeFormat` enums to `AVMetadataObjectType`:
     * `AVMetadataObjectTypeUPCECode`, `AVMetadataObjectTypeEAN8Code`, `AVMetadataObjectTypeEAN13Code`, `AVMetadataObjectTypeQRCode`, `AVMetadataObjectTypeCode128Code`, etc.
3. **Objective-C Delegate via `rubicon-objc`**:
   * Subclasses `NSObject` implementing `AVCaptureMetadataOutputObjectsDelegate`.
   * Overrides `captureOutput:didOutputMetadataObjects:fromConnection:`.
   * When a metadata object is detected, extracts `stringValue` and normalized `bounds`, marshals data into a `BarcodeResult`, and dispatches to the Python `on_barcode` callback on the asyncio event loop.
4. **UI Presentation**:
   * Instantiates an `AVCaptureVideoPreviewLayer` added to a modal `UIViewController` presented over `Toga`'s root view controller.
   * Implements custom overlay with semi-transparent scrim, scanning reticle box, and "Close" / "Flashlight" buttons.

#### iOS Permissions:
* Automatically documents the requirement for `NSCameraUsageDescription` in `Briefcase` configuration (`pyproject.toml` / `Info.plist`).

---

### 5.2. Android Backend (`toga_barcode_scanner.android`)

The Android implementation uses Google's modern **CameraX** library coupled with **Google ML Kit Barcode Scanning** (`com.google.mlkit:barcode-scanning`).

#### Architecture:
1. **CameraX Pipeline**:
   * `ProcessCameraProvider` handles camera lifecycle bound directly to the active Android `Activity`.
   * `Preview` use-case attaches to an Android `androidx.camera.view.PreviewView`.
   * `ImageAnalysis` use-case receives raw YUV image frames on a background `ExecutorService`.
2. **ML Kit Detection**:
   * Instantiates `BarcodeScannerOptions.Builder` with target barcode formats (`FORMAT_UPC_A`, `FORMAT_EAN_13`, `FORMAT_QR_CODE`, etc.).
   * Ingests `InputImage.fromMediaImage(mediaImage, rotationDegrees)`.
   * `addOnSuccessListener` decodes results and fires the Python bridge callback.
3. **Android Bridge**:
   * Communicates between Android Java runtime and Python via Chaquopy or PyJNIus.
   * Dispatches results back to Python on the main UI thread via `Activity.runOnUiThread`.
4. **Overlay & Viewfinder**:
   * A custom Android `FrameLayout` hosting the `PreviewView`, torch toggle floating action button (FAB), and viewfinder reticle.

#### Android Permissions:
* Declares `<uses-permission android:name="android.permission.CAMERA" />` and `<uses-feature android:name="android.hardware.camera" />`.
* Implements dynamic runtime permission requests (`ActivityCompat.requestPermissions`).

---

### 5.3. Dummy/Desktop Backend (`toga_barcode_scanner.dummy`)

To allow application developers to test on desktop workstations (`macOS`, `Windows`, `Linux`) without crashing:
1. **Mock Dialog**: Shows a mock dialog allowing manual entry of a barcode string or uploading an image file containing a barcode (using `pyzbar` or OpenCV if installed).
2. **Synthetic Event Injection**: Allows automated test suites to call `scanner._inject_barcode("012000000133", BarcodeFormat.UPC_A)` to simulate hardware events in headless CI pipelines.

---

## 6. SodaTry Integration Workflow

```python
# Example: Integrating Barcode Scanner into SodaTry mobile client
import toga
from toga_barcode_scanner import BarcodeScanner, BarcodeFormat, BarcodeResult
import httpx

class SodaTryMobileApp(toga.App):
    def startup(self):
        self.scanner = BarcodeScanner(
            app=self,
            on_barcode=self.handle_scanned_barcode,
            formats=[BarcodeFormat.UPC_A, BarcodeFormat.EAN_13, BarcodeFormat.UPC_E],
            beep_on_scan=True
        )
        
        self.scan_button = toga.Button(
            "Scan Soda Can/Bottle",
            on_press=self.start_scanning_flow
        )
        self.main_window = toga.MainWindow(title="SodaTry Mobile")
        self.main_window.content = self.scan_button
        self.main_window.show()

    def start_scanning_flow(self, widget):
        self.scanner.start_scan(parent_window=self.main_window)

    async def handle_scanned_barcode(self, result: BarcodeResult):
        self.scanner.stop_scan()
        upc = result.raw_value
        
        # Query SodaTry FastAPI backend
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"https://api.sodatry.com/api/sodas/barcode/{upc}")
            if resp.status_code == 200:
                soda = resp.json()
                await self.main_window.info_dialog(
                    "Soda Found!",
                    f"Brand: {soda['brand']}\nName: {soda['name']}\nStyle: {soda['style']}"
                )
            else:
                await self.main_window.error_dialog(
                    "Not Found",
                    f"No soda matched barcode {upc}. Would you like to add it?"
                )
```

---

## 7. Packaging & Dependency Configuration

### 7.1. `Briefcase` Configuration for Consumer Apps (`pyproject.toml`)

```toml
[tool.briefcase.app.sodatry.iOS]
info_plist_extra = { "NSCameraUsageDescription" = "SodaTry needs camera access to scan soda bottle and can barcodes." }
requires = [
    "toga-barcode-scanner>=0.1.0",
]

[tool.briefcase.app.sodatry.android]
permissions = [
    "android.permission.CAMERA",
]
gradle_dependencies = [
    "androidx.camera:camera-core:1.3.1",
    "androidx.camera:camera-camera2:1.3.1",
    "androidx.camera:camera-lifecycle:1.3.1",
    "androidx.camera:camera-view:1.3.1",
    "com.google.mlkit:barcode-scanning:17.2.0",
]
requires = [
    "toga-barcode-scanner>=0.1.0",
]
```

---

## 8. Security, Error Handling & Edge Cases

| Scenario / Edge Case | Mitigation & Handling |
| :--- | :--- |
| **Permission Denied** | Triggers `on_error("PERMISSION_DENIED")` and displays actionable prompt to open OS App Settings. |
| **No Camera Hardware** | Desktop/Simulator fallback gracefully degrades to dummy file/text entry. |
| **Rapid Double-Scanning** | Internal debouncing (300ms lock) ensures a single physical barcode does not trigger duplicate events. |
| **Low Light / Glare** | Built-in UI exposes a torch toggle button; native exposure lock minimizes reflection artifacts on shiny cans/bottles. |
| **Unsupported Symbology** | Filtered out at hardware level via `AVCaptureMetadataOutput` or ML Kit options, conserving CPU cycles. |

---

## 9. Verification & Testing Strategy

1. **Unit Testing (`pytest`)**:
   * Test core models, callback dispatching, validation logic, and debouncer using the `DummyBackend`.
2. **Platform Mock Testing**:
   * Mock `rubicon.objc` classes and verify correct delegate mapping for iOS.
   * Mock Android Java classes to verify `BarcodeResult` translation.
3. **End-to-End Simulator Verification**:
   * Run with `briefcase run iOS -d` on Xcode iOS Simulator with camera mock feed.
   * Run with `briefcase run android -d` on Android Virtual Device (AVD).
