#!/usr/bin/env bash
set -euo pipefail

image_path="$1"

mkfs.ext4 -O casefold -E encoding=utf8,encoding_flags=strict "$image_path"
