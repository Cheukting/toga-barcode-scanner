# Contributing to toga-barcode-scanner

Thank you for contributing to `toga-barcode-scanner`!

---

## 🛠️ Development Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-org/toga-barcode-scanner.git
   cd toga-barcode-scanner
   ```

2. **Create a virtual environment and install development dependencies**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -e ".[dev]"
   ```

3. **Run tests**:
   ```bash
   pytest
   ```

---

## 🌿 Branching & Git Workflow

- Always work on feature branches named `feature/<feature-name>` or `fix/<bug-name>`.
- Make small, atomic commits with descriptive commit messages.
- Always include automated unit tests when adding new features or fixing bugs.
- Do not commit directly to `main`. Open a Pull Request for review.
- Document any notable changes in `CHANGELOG.md`.

---

## 📝 Code Style & Standards

- Formatted using `black` and `isort`.
- Type annotations required on all public interfaces (`mypy` compatible).
- Follow PEP 8 guidelines and document public classes/methods with docstrings.
