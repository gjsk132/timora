#!/bin/bash
# Timora installer — double-click to run.
set -e

# Move to this script's own folder (works regardless of folder name/location).
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

echo "================================================"
echo "  Timora — installing"
echo "  Location: $DIR"
echo "================================================"
echo ""

# 1) Check for python3
if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 not found."
  echo "Run this in Terminal first to install the developer tools:"
  echo ""
  echo "       xcode-select --install"
  echo ""
  echo "When it finishes, double-click this file again."
  read -n 1 -s -r -p "Press any key to close..."
  exit 1
fi

# 2) Create a fresh virtual environment
echo "Creating a Python virtual environment..."
rm -rf venv
python3 -m venv venv

# 3) Install dependencies
echo "Installing packages... (this can take a minute or two)"
./venv/bin/python -m pip install --upgrade pip >/dev/null
./venv/bin/pip install -r requirements.txt

# 4) Point the app launcher at this folder
RUN="Timora.app/Contents/MacOS/run"
if [ -f "$RUN" ]; then
  cat > "$RUN" <<EOF
#!/bin/bash
# Detach python from the LaunchServices app context so it gets a menu bar slot.
DIR="$DIR"
cd "\$DIR" || exit 1
nohup "\$DIR/venv/bin/python" -m timora >/dev/null 2>&1 &
exit 0
EOF
  chmod +x "$RUN"
fi

echo ""
echo "================================================"
echo "  Done!"
echo ""
echo "  To run:"
echo "   - Double-click 'Timora.app'. A book icon appears in the menu bar."
echo "   - For quick access, move it to your Dock or Applications folder."
echo "================================================"
echo ""
read -n 1 -s -r -p "Press any key to close..."
