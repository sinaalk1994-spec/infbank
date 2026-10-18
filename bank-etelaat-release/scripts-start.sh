#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
exec .venv/bin/waitress-serve --listen=127.0.0.1:8000 --threads=4 config.wsgi:application
