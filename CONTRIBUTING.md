# Contributing to toga-barcode-scanner

Thank you for contributing to `toga-barcode-scanner`!

---

## 🛠️ Development Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Cheukting/toga-barcode-scanner.git
   cd toga-barcode-scanner
   ```

2. **Create a virtual environment and install development dependencies**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -e "."
   pip install --group dev
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

---

## 🚀 Releasing

To publish a new version to PyPI:

1. **Update the version** in `pyproject.toml`.
2. **Update `CHANGELOG.md`** with the new version and date.
3. **Commit and push** changes to `main`.
4. **Create and push a version tag**:
   ```bash
   git tag -a v0.1.2 -m "Release v0.1.2"
   git push origin v0.1.2
   ```

The release workflow will automatically run tests, build the distribution, and publish to PyPI using PyPI Trusted Publisher (OIDC authentication).

**One-time setup**: Before the first release, configure PyPI Trusted Publisher:

1. Go to your project on [PyPI](https://pypi.org/manage/projects/) → Publishers → Add trusted publisher.
2. Set **GitHub repository name** and **Workflow name** to `release.yml`.
3. Create a `pypi` environment in your GitHub repository Settings → Environments.
