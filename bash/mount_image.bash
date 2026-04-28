#!/usr/bin/env bash
set -euo pipefail

image_path="$1"
destination="$2"

sudo mount -o loop "$image_path" "$destination"
