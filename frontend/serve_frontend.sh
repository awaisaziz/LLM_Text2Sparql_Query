#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
PORT=${1:-4173}
python -m http.server "$PORT"
