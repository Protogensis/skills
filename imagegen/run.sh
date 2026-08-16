#!/bin/sh
# imagegen 官方 CLI 包装器：从 .env 读取中转站 key + base_url
# 支持通过软链（全局命令 / claude skill 目录）调用，自动解析到物理路径
set -e

SELF="$0"
while [ -L "$SELF" ]; do
  LINK="$(readlink "$SELF")"
  case "$LINK" in
    /*) SELF="$LINK" ;;
    *)  SELF="$(dirname "$SELF")/$LINK" ;;
  esac
done
# pwd -P 强制物理路径，避免目录级软链导致的路径分歧
DIR="$(cd "$(dirname "$SELF")" && pwd -P)"
ENV_FILE="$DIR/.env"

if [ ! -f "$ENV_FILE" ]; then
  echo "缺少 $ENV_FILE"
  echo "请先: cp '$DIR/.env.example' '$ENV_FILE' 并填入你的中转站 key"
  exit 1
fi
set -a
. "$ENV_FILE"
set +a
exec "$DIR/.venv/bin/python" "$DIR/scripts/image_gen.py" "$@"
