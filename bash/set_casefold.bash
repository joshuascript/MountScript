#!/usr/bin/env bash
set -euo pipefail

destination="$1"

sudo chattr +F "$destination"
