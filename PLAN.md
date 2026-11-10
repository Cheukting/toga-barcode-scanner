# Project Roadmap & Implementation Plan (`PLAN.md`)

This roadmap breaks down the construction of `toga-barcode-scanner` into structured, verifiable phases.

---

## 🎯 Phase 1: Core Architecture, Types & Dummy Backend (Current)
- [x] Initial repository setup with Git, `pyproject.toml`, and contribution docs.
- [x] Comprehensive technical design specification in `DESIGN.md`.
- [ ] Implement core models (`BarcodeFormat`, `BarcodeResult`, `ScanMode`, `CameraFacing`).
- [ ] Implement `BarcodeScanner` abstract interface and event dispatcher.
- [ ] Implement `DummyBackend` supporting desktop testing and synthetic test injection.
- [ ] Full unit test coverage for core interface and dummy backend with `pytest`.

---

## 🍏 Phase 2: iOS Native Backend (`AVFoundation` / `rubicon-objc`)
- [ ] Implement `toga_barcode_scanner.ios` backend using `rubicon-objc`.
- [ ] Implement `AVCaptureSession` and `AVCaptureMetadataOutput` wrappers.
- [ ] Implement Objective-C delegate for `AVCaptureMetadataOutputObjectsDelegate`.
- [ ] Build camera overlay with reticle box, torch toggle, and close action.
- [ ] Add camera permission checks (`AVCaptureDevice.authorizationStatusForMediaType:`).
- [ ] Verify on iOS Simulator via `briefcase run iOS`.

---

## 🤖 Phase 3: Android Native Backend (`CameraX` / Google `ML Kit`)
- [ ] Implement `toga_barcode_scanner.android` backend using Chaquopy / Android Java bridges.
- [ ] Configure Gradle dependencies for `androidx.camera` and `com.google.mlkit:barcode-scanning`.
- [ ] Implement `ImageAnalysis.Analyzer` connecting ML Kit to Python callbacks.
- [ ] Implement Android runtime permission requests.
- [ ] Build Android `PreviewView` overlay.
- [ ] Verify on Android Emulator via `briefcase run android`.

---

## 🧪 Phase 4: Integration with SodaTry & End-to-End Validation
- [ ] Import `toga-barcode-scanner` into `SodaTry` mobile client.
- [ ] Wire barcode scans directly to `FastAPI` endpoint `/api/sodas/barcode/{upc}`.
- [ ] Test automatic catalog discovery, tasting log auto-population, and missing barcode creation.
- [ ] Performance and latency benchmarking (<150ms scan latency target).

---

## 📦 Phase 5: CI/CD, Documentation & PyPI Release
- [ ] Configure GitHub Actions workflow running `pytest`, `flake8`, and `mypy`.
- [ ] Publish documentation site and PyPI package (`toga-barcode-scanner==0.1.0`).
- [ ] Submit integration example to BeeWare community showcase.
