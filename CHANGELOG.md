# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- Added MIT `LICENSE` file to the repository. The license was previously declared in `pyproject.toml` but the actual license text file was missing, which is required for proper PyPI distribution.
- Added wheel build and twine validation steps to the CI workflow to ensure both source distributions and wheels are correctly built and pass PyPI standards before release.

## [0.1.1] - 2026-11-12

### Changed
- Consolidated dependencies: moved all development tools (`pytest`, `black`, `isort`, `mypy`, `build`, `twine`) from `[project.optional-dependencies]` to PEP 735 `[dependency-groups]`. Only runtime extras (`ios`) remain in `[project.optional-dependencies]`. Updated CI workflow and CONTRIBUTING.md to use `pip install --group dev` syntax.

## [0.1.0] - 2026-11-10

### Changed
- Bumped minimum Python version from 3.9 to 3.13. Updated `pyproject.toml` classifiers, `README.md` badge, and CI workflow matrix to target Python 3.13.
- Consolidated all feature branches (`feature/implement-scanner-backend`, `feature/plugin-design-doc`, `bump-python-3.13`) into `main`. All 31 tests pass.

### Added
- Integration testing suite in `tests/test_integration.py` modeling SodaTry retail catalog discovery and tasting inventory scans.
- GitHub Actions CI workflow in `.github/workflows/ci.yml` matrix testing Python 3.13 across Linux and macOS runners.
- Briefcase packaging configuration templates in `README.md` for iOS permissions and Android CameraX / ML Kit Gradle dependencies.
- Native Android capture backend (`android.py`) using CameraX (`androidx.camera`) and Google ML Kit Barcode Scanning (`com.google.mlkit:barcode-scanning`).
- Background `ImageAnalysis.Analyzer` frame processor streaming decoded barcode symbologies to Python callbacks without blocking the UI thread.
- Android camera lifecycle management, torch controls, and asynchronous runtime camera permission handling (`ActivityCompat.requestPermissions`).
- Comprehensive Android unit tests in `tests/test_android.py`.
- Native iOS capture backend (`ios.py`) utilizing `rubicon-objc`, `AVFoundation`, and `UIKit`.
- Objective-C delegate `BarcodeCaptureDelegate` parsing `AVCaptureMetadataOutput` objects and mapping native metadata symbologies to `BarcodeFormat` types.
- iOS modal viewfinder `UIViewController` with camera preview layer, reticle overlay, torch toggle button, and dismiss action.
- Asynchronous iOS camera permission acquisition using `AVCaptureDevice.requestAccessForMediaType:completionHandler:`.
- Backend factory layer (`factory.py`) with `BaseBarcodeScannerBackend` contract and dynamic platform backend resolution.
- Desktop and headless dummy testing backend (`dummy.py`) with synthetic event injection (`_inject_barcode`) and mock permission controls.
- Core coordinator delegation in `BarcodeScanner` (`core.py`) with configurable debounce protection, format filtering, and error event routing.
- Comprehensive unit test suite in `tests/test_factory.py`, `tests/test_dummy.py`, and `tests/test_core.py`.
- Initial project architecture and design document (`DESIGN.md`).
- Core API abstraction design for BeeWare/Toga barcode scanner plugin.
- Native backend specifications for iOS (`AVFoundation` / `rubicon-objc`) and Android (`CameraX` / `ML Kit`).
- Project roadmap and milestones (`PLAN.md`).
- Developer setup and contribution guidelines (`CONTRIBUTING.md`).
- Core data models (`BarcodeFormat`, `BarcodeResult`, `ScanMode`, `CameraFacing`).
