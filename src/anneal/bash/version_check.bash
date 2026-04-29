#!/usr/bin/env bash
set -euo pipefail

version=$(mkfs.ext4 -V 2>&1 | awk 'NR==1{print $2; exit}')

if [[ -z "$version" ]]; then
    echo "could not determine e2fsprogs version" >&2
    exit 1
fi

echo "$version"
