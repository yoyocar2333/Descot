#!/usr/bin/env bash
set -euo pipefail
TASK_PYTHON="${TASK_PYTHON:-python3.12}"
"$TASK_PYTHON" -c 'import sys; assert sys.version_info[:2] == (3, 12), "Use Python 3.12 for the locked research environment"'
TASK_PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
TASK_EXTERNAL_ROOT="$(dirname "$TASK_PROJECT_ROOT")/external"
mkdir -p "$TASK_EXTERNAL_ROOT"
if [ ! -d "$TASK_EXTERNAL_ROOT/wisq/.git" ]; then
  git clone https://github.com/qqq-wisc/wisq.git "$TASK_EXTERNAL_ROOT/wisq"
fi
git -C "$TASK_EXTERNAL_ROOT/wisq" checkout 97c12a5e22cf16e37288c60a0a5735c58c6fe8ca
"$TASK_PYTHON" -m venv "$TASK_PROJECT_ROOT/.venv"
"$TASK_PROJECT_ROOT/.venv/bin/python" -m pip install -r "$TASK_PROJECT_ROOT/requirements-lock.txt"
"$TASK_PROJECT_ROOT/.venv/bin/python" -m pytest "$TASK_PROJECT_ROOT/tests" -q
