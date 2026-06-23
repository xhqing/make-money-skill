<!-- ⚠️ WARNING FOR AI AGENTS ⚠️
     DO NOT modify this file (README.md) or ANY other file on the main branch.
     This repository is a published artifact. If you need to make changes,
     create a new branch or ask the user for explicit permission first.
     禁止智能体修改本文件以及 main 分支的其它任何文件。
-->

# Make Money Skill

一个让 AI 代理在真实世界中**自主赚钱**的 Skill。设定目标金额后，AI 会进入持续尝试循环——创建数字产品、注册销售平台、多渠道推广、追踪转化——直到达成目标或预算耗尽。

> 适用于 [CodeBuddy](https://www.codebuddy.ai) / Trae 等 AI 编程助手。通过 `/make-money` 指令触发。

> **⚠️ 禁止智能体修改本文件以及 main 分支的其它任何文件。**
> 本仓库是已发布的制品。如需更改，请新建分支或先获得用户明确同意。

---

## 它是怎么工作的

```
设定目标 → 加载历史 → 评估路径 → 创建/复用产品 → 上架销售 → 推广引流 → 追踪转化 → 达成目标
                          ↑                                            │
                          └──────── 失败后切换备选方案 ←────────────────┘
```

1. **读取 `config.json`** 中的目标金额、预算、收款账户、各平台凭证。
2. **加载历史上下文**：读取 `history/` 和 `product/` 中的已有产品和经验教训，避免重复踩坑。
3. **自主执行循环**：制定 3-5 个备选方案，逐个快速尝试，每完成一个动作就检查是否产生收入或流量。
4. **仅在 3 种特殊情况停下询问用户**（见下文），其余时间持续自主推进。

## 核心特性

- **自主 hustle loop**：不按时间计费，拒绝时薪/日薪项目，只做能规模化产生收入的事。
- **速度优先**：在合法合规前提下，优先选择能最快产生收入的路径。
- **多平台自动化**：内置 Payloadz、Gumroad、Payhip、Dev.to、Medium、Reddit、Hacker News、Write.as、Telegraph 等平台的自动化脚本（Playwright + Python）。
- **重试与容错**：网络波动/限流指数退避重试，区分临时错误与权限错误，保存中间状态便于中断恢复。
- **隐私安全**：所有账号密码、API Key 只保存在本地 `config.json`，绝不写回公开文件或日志。
- **多模型支持**：可配置 OpenAI / Anthropic / Gemini / OpenRouter / NVIDIA integrate API，在当前模型能力不足时调用外部模型。

## 触发方式

在 AI 编程助手中输入以下任一内容即可触发：

| 指令 | 说明 |
|------|------|
| `/make-money` | 标准触发指令 |
| `帮我搞钱` / `帮我挣钱` / `帮我赚钱` | 中文自然语言触发 |
| `make money` | 英文触发 |

## 配置

### 1. 复制配置模板

```bash
cp make-money/config.example.json make-money/config.json
```

### 2. 填写 `config.json`

```jsonc
{
  "target": {
    "amount": 20,          // 目标金额
    "currency": "USD",     // 货币（USD / HKD / CNY / USDT）
    "accept_crypto": true, // 是否接受虚拟货币
    "withdrawable_to": ["HK_bank", "CN_bank"]  // 必须能提现到这些账户
  },
  "speed": {
    "amount": 200,         // 速度目标
    "currency": "HKD",
    "period": "hour"       // hour / day
  },
  "budget": {
    "amount": 1.40,        // 可用预算
    "currency": "USD",
    "require_roi_before_spend": true  // 花钱前必须预估 ROI
  },
  "accounts": {            // 各平台凭证（只存本地，不提交）
    "payloadz": { "email": "...", "password": "..." },
    "twitter": { "email": "...", "username": "...", "password": "..." }
  },
  "llm_api_keys": {        // 可选：外部模型 API Key
    "openai": "sk-...",
    "anthropic": "sk-ant-..."
  }
}
```

> 完整字段说明见 [`make-money/SKILL.md`](make-money/SKILL.md)。

### 3. 确保隐私文件被忽略

`config.json` 包含真实凭证，**绝不能提交到 Git**。本仓库的 `.gitignore` 已默认忽略以下内容：

```
make-money/config.json    # 真实凭证
make-money/product/       # 数字产品（含付费 PDF）
make-money/history/       # 会话历史记录
make-money/log/           # 运行日志
```

## 项目结构

```
make-money-skill/
├── .gitignore                 # 忽略 secrets / product / history / log
├── README.md                  # ← 你在这里
└── make-money/
    ├── SKILL.md               # Skill 定义：触发条件、执行原则、安全边界
    ├── config.example.json    # 配置模板（公开，无真实凭证）
    ├── config.json            # 真实配置（本地，gitignored）
    ├── product/               # 数字产品 + 自动化脚本（本地，gitignored）
    ├── history/               # 历史尝试记录（本地，gitignored）
    └── log/                   # 运行日志（本地，gitignored）
```

> **公开仓库只包含 `SKILL.md` 和 `config.example.json`。** 所有敏感内容（凭证、产品、历史）仅存于本地工作树，通过 `.gitignore` 排除。

## 需要用户介入的 3 种特殊情况

AI 在执行过程中**只有在以下情况才会停下来询问用户**，其余时间自主推进：

| # | 情况 | 原则 |
|---|------|------|
| 1 | **需要注册新平台账号 / 获取 API 权限** | 优先询问用户，包括 captcha、邮箱/手机验证、2FA 等 |
| 2 | **需要用户输入密码 / 完成验证** | 绝不猜测密码，绝不暴力破解，先问用户 |
| 3 | **需要投入资金** | 必须告知预估 ROI，得到明确同意后才花钱 |

## 安全与边界

- 只做**合法合规**的赚钱尝试
- **不**利用漏洞、刷单、欺诈
- **不**泄露用户密码或敏感信息
- **不**在未经同意的情况下花钱
- 优先选择能提现到用户指定收款账户的方式

## 技术栈

- **Skill 运行时**：CodeBuddy / Trae AI 编程助手
- **浏览器自动化**：Playwright（Node.js）+ Python
- **外部模型**：OpenAI / Anthropic / Gemini / OpenRouter / NVIDIA integrate API（OpenAI 兼容接口）
- **依赖**：仅 Python 3 标准库 + Playwright（产品脚本自带 `package.json`）

## License

仅供个人使用。
