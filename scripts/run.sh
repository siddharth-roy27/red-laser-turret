#!/bin/bash
set -e
cd "$(dirname "$0")/.."
# Run main; use exec so process replaces the shell (better for systemd)
exec python3 -m src.main
