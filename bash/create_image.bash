#!/usr/bin/env bash
set -euo pipefail

image_path="$1"
size_gb="${2:-50}"

truncate -s "${size_gb}G" "$image_path"
