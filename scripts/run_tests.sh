#!/usr/bin/env bash
# Bash script to run all tests (Python backend + Flutter Mini App)
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
FLUTTER_DIR="$ROOT_DIR/frontend_flutter"

echo -e "\033[0;36m=============================================\033[0m"
echo -e "\033[0;36m Gravigram Automated Test Suite Runner\033[0m"
echo -e "\033[0;36m=============================================\033[0m"

cd "$ROOT_DIR"

# 1. Python Backend Tests
echo -e "\n\033[0;33m[1/2] Running Python Backend Tests (pytest)...\033[0m"

PYTEST_CMD="pytest"
if [ -f "$ROOT_DIR/venv/bin/pytest" ]; then
    PYTEST_CMD="$ROOT_DIR/venv/bin/pytest"
elif [ -f "$ROOT_DIR/.venv/bin/pytest" ]; then
    PYTEST_CMD="$ROOT_DIR/.venv/bin/pytest"
fi

$PYTEST_CMD -v
echo -e "\033[0;32m✅ Python tests passed!\033[0m"

# 2. Flutter Mini App Tests
echo -e "\n\033[0;33m[2/2] Running Flutter Mini App Tests (flutter test)...\033[0m"

if command -v flutter &> /dev/null; then
    cd "$FLUTTER_DIR"
    flutter test
    echo -e "\033[0;32m✅ Flutter tests passed!\033[0m"
    cd "$ROOT_DIR"
else
    echo -e "\033[0;33m⚠️ 'flutter' command not found in PATH. Skipping Flutter tests.\033[0m"
fi

echo -e "\n\033[0;32m=============================================\033[0m"
echo -e "\033[0;32m🎉 All tests completed successfully!\033[0m"
echo -e "\033[0;32m=============================================\033[0m"
