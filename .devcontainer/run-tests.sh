#!/usr/bin/env bash
set -euo pipefail

cd /workspaces/tethysext-atcore

# Find manage.py inside the image
MANAGE="${TETHYS_MANAGE:-}"
if [ -z "$MANAGE" ] || [ ! -f "$MANAGE" ]; then
  for p in \
    /usr/lib/tethys/manage.py \
    /usr/lib/tethys/tethys_portal/manage.py \
    /var/lib/tethys/tethys_portal/manage.py \
    /var/lib/tethys/tethys/tethys_portal/manage.py \
    /var/www/tethys/tethys_portal/manage.py
  do
    [ -f "$p" ] && MANAGE="$p" && break
  done
fi
if [ -z "$MANAGE" ] || [ ! -f "$MANAGE" ]; then
  MANAGE="$(find /usr/lib/tethys /var/lib/tethys /var/www/tethys -type f -name manage.py 2>/dev/null | head -n 1 || true)"
fi

echo "Using manage.py: $MANAGE"
test -f "$MANAGE"

source ci-test.sh "$MANAGE"
