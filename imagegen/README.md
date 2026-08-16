# imagegen — Agent 生图技能

适用于 Claude Code / Codex 及所有支持 `SKILL.md` 规范的 agent 的图像生成与编辑技能。三条通道：

| 通道 | 模型 | 用途 |
|---|---|---|
| 内置 `image_gen` 工具 | — | 默认优先，无需 key（Codex 内置） |
| 官方 CLI fallback | `gpt-image-2` | 显式指定 API 路径时，需 `OPENAI_API_KEY` |
| Grok 通道（扩展） | `grok-imagine-image-quality` 等 | 走 OpenAI 兼容中转站的备用生图通道 |

## 安装

本技能是 [skills 合集仓库](https://github.com/Protogensis/skills) 的一个子目录。

**skills CLI（自动处理子目录）：**

```sh
npx skills add Protogensis/skills/imagegen
```

**手动 clone + 软链：**

```sh
git clone https://github.com/Protogensis/skills.git ~/tmp-skills
ln -s ~/tmp-skills/imagegen ~/.claude/skills/imagegen
```

或跨 agent 标准路径：

```sh
ln -s ~/tmp-skills/imagegen ~/.agents/skills/imagegen
```

## 配置

1. 安装依赖（官方 CLI 与 Grok 通道共用一个 venv）：

   ```sh
   cd <skill目录>
   uv venv
   uv pip install openai pillow
   ```

2. 复制并填写密钥（**推荐放 `~/.config/imagegen/.env`**，技能更新/重装不会丢）：

   ```sh
   mkdir -p ~/.config/imagegen
   cp .env.example ~/.config/imagegen/.env
   ```

   ```ini
   OPENAI_API_KEY=你的key          # 官方或中转站
   OPENAI_BASE_URL=https://.../v1  # 必须以 /v1 结尾；官方可省略
   GROK_API_KEY=                   # Grok 通道（可选）
   GROK_IMAGE_MODEL=grok-imagine-image-quality
   GROK_EDIT_MODEL=grok-imagine-edit
   ```

   `.env` 已被 `.gitignore` 排除，密钥不会入库。

## 使用

日常让 agent 自主调用即可（"生成一张…" / "把这张图的背景换成…"）。手动执行：

```sh
# 官方通道
run.sh generate --prompt "..." --out out.png
run.sh generate-batch --prompts-file jobs.jsonl --out-dir output/imagegen/

# Grok 通道
grok.sh generate --prompt "..." --quality high --out out.png
grok.sh generate --prompt "..." --aspect-ratio 16:9 --out out.png
grok.sh edit --image 原图.png --prompt "..." --out out.png
```

## 已知差异（Grok 通道实测）

- 尺寸参数只有 `--aspect-ratio W:H|auto`（默认 auto；经 `extra_body` 透传，中转站支持）；无 `--size`
- 返回 URL 时脚本已带浏览器 UA 下载（部分图床 403 python 默认 UA）
- `grok-imagine-edit` 可能因中转站上游池缺账号报 503，编辑需求可临时用官方通道替代

## 致谢与许可

官方通道部分派生自 [OpenAI Codex](https://github.com/openai/codex) 内置 imagegen 技能。

Grok 通道扩展及中转站适配为本仓库添加。均以 [Apache-2.0](LICENSE) 发布。
