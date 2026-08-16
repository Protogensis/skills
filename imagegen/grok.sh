#!/bin/sh
# grok 生图包装器：从 .env 读取 base_url + GROK_API_KEY
set -e
SELF="$0"
while [ -L "$SELF" ]; do
  LINK="$(readlink "$SELF")"
  case "$LINK" in
    /*) SELF="$LINK" ;;
    *)  SELF="$(dirname "$SELF")/$LINK" ;;
  esac
done
DIR="$(cd "$(dirname "$SELF")" && pwd -P)"
ENV_FILE="$DIR/.env"
if [ ! -f "$ENV_FILE" ]; then
  echo "缺少 $ENV_FILE"; exit 1
fi
set -a; . "$ENV_FILE"; set +a
exec "$DIR/.venv/bin/python" "$DIR/scripts/grok_gen.py" "$@"
