---
name: sync-skill
description: "双向目录同步器，支持 Git 分支。通过 /sync-skill 命令触发。读取一个 JSON 配置文件，其中指定两个目录（各自可选 Git 分支），在两者之间同步所有内容——双向复制新文件、用较新版本更新较旧文件、同步前切换到配置的 Git 分支、同步后提交并推送变更。分支值为空的目录会被视为普通非 Git 目录（仅做文件同步）。当用户输入 /sync-skill 或要求在两个位置或分支之间同步 skill 目录时，使用此 skill。"
---

# Sync Skill

## 概述

在两个目录之间同步内容，每个目录可选支持 Git 分支。当用户执行 `/sync-skill` 时，运行内置的 `scripts/sync_skill.py` 脚本，它会自动完成全部同步流程。

## 配置

脚本会按以下顺序查找 JSON 配置文件（命中第一个即停止）：

1. `.codebuddy/skills/sync-skill/.sync-skill.json`（本 skill 目录内的配置）
2. `$CLAUDE_PROJECT_DIR/.sync-skill.json`
3. `./.sync-skill.json`（当前工作目录）
4. `~/.codebuddy/sync-skill-config.json`

### 配置格式

```json
{
  "side_a": {
    "path": "/absolute/path/to/directory-a",
    "branch": "main"
  },
  "side_b": {
    "path": "/absolute/path/to/directory-b",
    "branch": ""
  },
  "exclude": [".git", "node_modules", "__pycache__", ".DS_Store"]
}
```

| 字段 | 必填 | 说明 |
|-------|----------|-------------|
| `side_a.path` | 是 | 第一个目录的绝对路径。 |
| `side_a.branch` | 否 | 同步前要切换的 Git 分支。**留空或省略 = 非 Git 目录**（仅做文件同步）。 |
| `side_b.path` | 是 | 第二个目录的绝对路径。 |
| `side_b.branch` | 否 | B 端的 Git 分支。规则同 `side_a.branch`。 |
| `exclude` | 否 | 同步时要跳过的目录/文件名列表。默认值为 `[".git"]`。 |



### 关键规则

- **分支为空 → 非 Git 目录**：如果 `branch` 为 `""` 或未设置，该目录会被视为普通文件夹，不执行任何 Git 操作。
- **分支已设置 → Git 目录**：该目录必须是一个 Git 仓库。脚本会切换到配置的分支（必要时创建）、拉取最新内容，同步后再提交并推送变更。

## 工作流程

当用户触发 `/sync-skill` 时：

1. **检查配置是否存在。** 如果找不到配置文件，告知用户预期的查找位置。

2. **运行同步脚本。**
   ```bash
   python3 <skill-dir>/scripts/sync_skill.py
   ```
   脚本会：
   - 加载并校验配置。
   - 对每个有非空分支的一端：确认是 Git 仓库，切换到目标分支（必要时创建），并拉取最新内容。
   - 执行双向文件同步：
     - 仅存在于某一端的文件 → 复制到另一端。
     - 两端都存在的文件 → 以较新的版本（按修改时间）为准。
     - 永远不会自动删除任何文件（防止数据丢失）。
   - 对每个 Git 端：执行 `git add -A`、用带时间戳的信息提交。

3. **报告结果。** 汇总复制/更新了哪些文件以及执行了哪些 Git 操作。如果脚本以错误退出，显示错误信息并给出修复建议。

## 重要提示

- 同步是**双向的**——两个目录最终都会拥有所有文件的并集，冲突以最新修改时间解决。
- **删除不会传播。** 如果从一端删除了某个文件，下次同步时它会从另一端被复制回来、重新出现。要永久删除一个文件，需要在*两端*同时删除。
- 脚本仅使用 Python 3 标准库——无需 pip install。
