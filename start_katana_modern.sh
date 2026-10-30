#!/bin/bash
# Start script for Katana Modern Editor
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"
python3 "$DIR/run_modern_editor.py" "$@"
