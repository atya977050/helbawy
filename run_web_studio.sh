#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

echo "=============================================="
echo " عبقرينو — Web Studio"
echo "=============================================="
echo
echo "افتح في المتصفح:"
echo "http://127.0.0.1:8787"
echo
echo "Termux يعمل كمحرك خلفي فقط."
echo "=============================================="
echo

python3 studio/server.py
