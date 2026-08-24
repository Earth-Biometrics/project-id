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

if [[ "$OS" == "Linux" && "$ARCH" == "aarch64" ]]; then
  echo "==> Linux ARM64 detected (Spark Station path)"
  echo "==> Installing all deps except megadetector first"

  TMP_REQ="$(mktemp)"
  # Remove only the megadetector pinned line
  grep -vE '^[[:space:]]*megadetector==' "$REQ_FILE" > "$TMP_REQ"

  python -m pip install -r "$TMP_REQ"
  rm -f "$TMP_REQ"

  echo "==> Installing megadetector without dependency resolution (MKL workaround)"
  python -m pip install megadetector==10.0.24 --no-deps
else
  echo "==> Installing full requirements normally"
  python -m pip install -r "$REQ_FILE"
fi

echo "==> Optional: register Jupyter kernel"
python -m ipykernel install --user --name project-id-312 --display-name "Python 3.12 (project-id)"

echo "==> Smoke test imports"
python - <<'PY'
import numpy, pandas, PIL, torch, torchvision, matplotlib
import megadetector
print("OK: imports succeeded")
print("Python:", __import__("sys").version.split()[0])
print("Torch:", torch.__version__)
print("MegaDetector:", getattr(megadetector, "__version__", "installed"))
PY

echo
echo "Done."
echo "Activate with: source \"$VENV_DIR/bin/activate\""