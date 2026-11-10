# Project Roadmap & Implementation Plan (`PLAN.md`)

This roadmap breaks down the construction of `toga-barcode-scanner` into structured, verifiable phases.

---

## 🎯 Phase 1: Core Architecture, Types & Dummy Backend (Completed)
- [x] Initial repository setup with Git, `pyproject.toml`, and contribution docs.
- [x] Comprehensive technical design specification in `DESIGN.md`.
- [x] Implement core models (`BarcodeFormat`, `BarcodeResult`, `ScanMode`, `CameraFacing`).
- [x] Implement `BarcodeScanner` abstract interface and event dispatcher.
- [x] Implement `DummyBackend` supporting desktop testing and synthetic test injection.
- [x] Full unit test coverage for core interface and dummy backend with `pytest`.

---

## 🍏 Phase 2: iOS Native Backend (`AVFoundation` / `rubicon-objc`) (Completed)
- [x] Implement `toga_barcode_scanner.ios` backend using `rubicon-objc`.
- [x] Implement `AVCaptureSession` and `AVCaptureMetadataOutput` wrappers.
- [x] Implement Objective-C delegate for `AVCaptureMetadataOutputObjectsDelegate`.
- [x] Build camera overlay with reticle box, torch toggle, and close action.
- [x] Add camera permission checks (`AVCaptureDevice.authorizationStatusForMediaType:`).
- [x] Verify on iOS Simulator via `briefcase run iOS`.

---

## 🤖 Phase 3: Android Native Backend (`CameraX` / Google `ML Kit`) (Completed)
- [x] Implement `toga_barcode_scanner.android` backend using Chaquopy / Android Java bridges.
- [x] Configure Gradle dependencies for `androidx.camera` and `com.google.mlkit:barcode-scanning`.
- [x] Implement `ImageAnalysis.Analyzer` connecting ML Kit to Python callbacks.
- [x] Implement Android runtime permission requests.
- [x] Build Android `PreviewView` overlay.
- [x] Verify on Android Emulator via `briefcase run android`.

---

## 🧪 Phase 4: Integration with SodaTry & End-to-End Validation (Completed)
- [x] Import `toga-barcode-scanner` into `SodaTry` mobile client.
- [x] Wire barcode scans directly to `FastAPI` endpoint `/api/sodas/barcode/{upc}`.
- [x] Test automatic catalog discovery, tasting log auto-population, and missing barcode creation.
- [x] Performance and latency benchmarking (<150ms scan latency target).

---

## 📦 Phase 5: CI/CD, Documentation & PyPI Release (Completed)
- [x] Configure GitHub Actions workflow running `pytest`, `flake8`, and `mypy`.
- [x] Publish documentation site and PyPI package (`toga-barcode-scanner==0.1.0`).
- [x] Submit integration example to BeeWare community showcase.
