#!/usr/bin/env bash
set -euo pipefail

NET=crowdmind_net

if ! docker network inspect "$NET" >/dev/null 2>&1; then
  docker network create "$NET"
  echo "created network $NET"
else
  echo "network $NET already exists"
fi
