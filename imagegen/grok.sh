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
XDG_ENV="${XDG_CONFIG_HOME:-$HOME/.config}/imagegen/.env"
# .env 查找顺序：$IMAGEGEN_ENV 显式指定 > 技能目录(本地开发/旧版兼容) > ~/.config/imagegen/.env(技能更新/重装不丢)
if [ -n "$IMAGEGEN_ENV" ] && [ -f "$IMAGEGEN_ENV" ]; then
  ENV_FILE="$IMAGEGEN_ENV"
elif [ -f "$DIR/.env" ]; then
  ENV_FILE="$DIR/.env"
elif [ -f "$XDG_ENV" ]; then
  ENV_FILE="$XDG_ENV"
else
  echo "缺少 .env（依次找过: \$IMAGEGEN_ENV, $DIR/.env, $XDG_ENV）"
  echo "推荐放到技能更新不会覆盖的位置: cp '$DIR/.env.example' '$XDG_ENV' 并填入你的 key"
  exit 1
fi
set -a; . "$ENV_FILE"; set +a
exec "$DIR/.venv/bin/python" "$DIR/scripts/grok_gen.py" "$@"
