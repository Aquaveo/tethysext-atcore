#!/usr/bin/env bash
set -euo pipefail

cd /workspaces/tethysext-atcore

echo "== DB configure =="
micromamba run -n tethys tethys db configure

echo "== Install extension (editable) =="
micromamba run -n tethys tethys install -d -q -w

# Test fixture your CI expects
touch tethysext/atcore/tests/files/arc_grid/precip30min.* || true

echo "== Ready. To run tests: =="
echo "  bash .devcontainer/run-tests.sh"
