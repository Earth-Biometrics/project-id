#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   bash setup_spark_station.sh /work/git/ebio/project-id
# If no path is provided, uses current directory.
# or
# chmod +x setup_spark_station.sh
# then run: ./setup_spark_station.sh

REPO_DIR="${1:-$(pwd)}"
REQ_FILE="$REPO_DIR/requirements.txt"
VENV_DIR="$REPO_DIR/.venv312"

echo "==> Repo: $REPO_DIR"
echo "==> Requirements: $REQ_FILE"

if [[ ! -f "$REQ_FILE" ]]; then
  echo "ERROR: requirements.txt not found at: $REQ_FILE"
  exit 1
fi

if ! command -v python3.12 >/dev/null 2>&1; then
  echo "ERROR: python3.12 is not installed or not on PATH"
  exit 1
fi

echo "==> Creating clean Python 3.12 venv at $VENV_DIR"
python3.12 -m venv --clear "$VENV_DIR"

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

echo "==> Upgrading pip/setuptools/wheel"
python -m pip install --upgrade pip setuptools wheel

ARCH="$(uname -m)"
OS="$(uname -s)"

echo "==> Platform detected: $OS / $ARCH"

echo "==> Installing base requirements"
python -m pip install -r "$REQ_FILE"

# MegaDetector v6 lives in the vendored checkout and is installed in editable
# mode (pulls in PytorchWildlife/ultralytics via its pyproject.toml).
MD_DIR="$REPO_DIR/third-party/eb_MegaDetector_v6"
if [[ -d "$MD_DIR" ]]; then
  echo "==> Installing MegaDetector v6 (editable) from $MD_DIR"
  python -m pip install -e "$MD_DIR"
else
  echo "WARN: $MD_DIR not found; skipping MegaDetector v6 install."
  echo "      Clone it first (see notebooks/01_setup_megadetector.ipynb)."
fi

echo "==> Optional: register Jupyter kernel"
python -m ipykernel install --user --name project-id-312 --display-name "Python 3.12 (project-id)"

echo "==> Smoke test imports"
python - <<'PY'
import numpy, pandas, PIL, torch, torchvision, matplotlib
print("OK: core imports succeeded")
print("Python:", __import__("sys").version.split()[0])
print("Torch:", torch.__version__)
try:
    from megadetector_ai import MegaDetectorV6
    print("MegaDetector v6: megadetector_ai import OK")
except Exception as exc:
    print("MegaDetector v6: NOT importable ->", exc)
PY

echo
echo "Done."
echo "Activate with: source \"$VENV_DIR/bin/activate\""