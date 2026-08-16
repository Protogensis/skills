# skills

我的 Agent 技能合集（Claude Code / Codex / Cursor 等支持 `SKILL.md` 规范的 agent 通用）。

每个技能一个子目录，`SKILL.md` 在子目录根部——这是 [anthropics/skills](https://github.com/anthropics/skills) 确立的社区标准结构，各大技能市场按此索引。

## 技能列表

| 技能 | 说明 |
|---|---|
| [imagegen](./imagegen/) | 图像生成与编辑：gpt-image-2 官方 CLI + Grok 中转站双通道 |

## 安装

**单个技能（skills CLI，自动处理子目录）：**

```sh
npx skills add Protogensis/skills/<技能名>
```

**全部技能：**

```sh
git clone https://github.com/Protogensis/skills.git ~/skills
# 按需软链到对应 agent 的技能目录，例如：
ln -s ~/skills/imagegen ~/.claude/skills/imagegen
```

## 目录约定

```text
skills/
└── <技能名>/
    ├── SKILL.md        # 技能入口（agent 读取）
    ├── README.md       # 面向人的说明
    ├── references/     # 参考文档
    ├── scripts/        # 脚本
    └── ...
```

密钥类配置不入库：仓库只放 `.env.example` 模板，`.env` 一律不入库、不随技能分发。`.env` 推荐放技能目录外，避免更新/重装丢失——imagegen 的做法：放 `~/.config/imagegen/.env`，wrapper 依次查找 `$IMAGEGEN_ENV` → 技能目录 `.env` → `~/.config/imagegen/.env`。

## 许可

各技能许可见其目录内 `LICENSE`。无特别声明的技能按 Apache-2.0 发布。
