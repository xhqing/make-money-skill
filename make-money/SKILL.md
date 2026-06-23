---
name: "make-money"
description: "Helps the user earn money online by executing an autonomous hustle loop. Invoke when the user types '/make-money' or says phrases like '帮我搞钱', '帮我挣钱', '帮我赚钱', 'make money', or similar direct requests to earn money."
---

# Make Money

## 触发条件

当用户输入 `/make-money` 或直接说出以下意图时触发本 SKILL：
- "/make-money"
- "帮我搞钱"
- "帮我挣钱"
- "帮我赚钱"
- "make money"
- 任何明确表达"希望我在真实世界中尝试赚钱"的请求

## 核心目标

通过配置文件设定目标后，进入持续尝试循环，**除非遇到以下 3 种特殊情况，否则不要停下来汇报或询问用户**，不断尝试直到达成目标为止。

## 配置文件

读取配置文件：`.trae/skills/make-money/config.json`

> **文件内容优先级**：`config.json` 和 `SKILL.md` 的内容优先级高于 `make-money/` 目录下其它任何文件。如果其它文件内容与 `config.json` 或 `SKILL.md` 存在矛盾，一律以 `config.json` 和 `SKILL.md` 为准。

配置项示例：

```json
{
  "target": {
    "amount": 20,
    "currency": "USD",
    "accept_crypto": true,
    "withdrawable_to": ["HK_bank", "CN_bank"]
  },
  "speed": {
    "amount": 200,
    "currency": "HKD",
    "period": "hour"
  },
  "budget": {
    "amount": 1.40,
    "currency": "USD",
    "require_roi_before_spend": true
  },
  "assets": {
    "product_dir": "make-money-skill/product",
    "history_dir": "make-money-skill/history",
    "log_dir": "make-money-skill/log"
  },
  "accounts": {
    "gumroad": {
      "email": "",
      "password": ""
    },
    "payhip": {
      "email": "",
      "password": ""
    },
    "payloadz": {
      "email": "",
      "password": ""
    },
    "twitter": {
      "email": "",
      "username": "",
      "password": "",
      "api_key": "",
      "api_secret": "",
      "access_token": "",
      "access_token_secret": ""
    }
  },
  "llm_api_keys": {
    "openai": "sk-xxxxxxxx",
    "anthropic": "sk-ant-xxxxxxxx",
    "gemini": "AIzaSyxxxxxxxx",
    "openrouter": "sk-or-xxxxxxxx",
    "nvidia": {
      "api_key": "nvapi-xxxxxxxx",
      "invoke_url": "https://integrate.api.nvidia.com/v1/chat/completions",
      "model": "minimaxai/minimax-m3",
      "max_tokens": 8192,
      "temperature": 1.00,
      "top_p": 0.95,
      "supports_stream": true,
      "supports_multimodal": true
    }
  }
}
```

### 配置项说明

- `target`: 金额目标
  - `amount`: 目标金额数值
  - `currency`: 目标货币（USD / HKD / CNY / USDT 等）
  - `accept_crypto`: 是否接受虚拟货币
  - `withdrawable_to`: 必须能提现到支持的收款账户
- `speed`: 挣钱速度目标
  - `amount`: 单位时间收益数值
  - `currency`: 收益货币
  - `period`: 时间单位（hour / day）
- `budget`: 可用预算
  - `amount`: 预算金额
  - `currency`: 预算货币
  - `require_roi_before_spend`: 花钱前是否要求预估 ROI
- `assets`: 本地资产目录
  - `product_dir`: 已有产品/搞钱尝试目录
  - `history_dir`: 历史记录目录
  - `log_dir`: 搞钱日志目录
- `accounts`: 各平台账号凭证
  - `gumroad`: `email`, `password`
  - `payhip`: `email`, `password`
  - `payloadz`: `email`, `password`
  - `twitter`: `email`, `username`, `password`，以及 Twitter API 相关的 `api_key`, `api_secret`, `access_token`, `access_token_secret`
  - **注意**：账号密码等敏感信息只保存在本地 `config.json` 中，不要写回 `SKILL.md` 或日志
- `llm_api_keys`: 多个大模型 API Key
  - 当当前模型能力不足或需要调用外部模型服务时，可使用这些 Key
  - 支持 OpenAI、Anthropic、Gemini、OpenRouter 等
  - `nvidia`: NVIDIA integrate API（支持多模态、文本、图片、视频），包含：
    - `api_key`: `nvapi-` 开头的 NVIDIA API Key
    - `invoke_url`: 默认 `https://integrate.api.nvidia.com/v1/chat/completions`
    - `model`: 模型名（例如 `minimaxai/minimax-m3`）
    - `max_tokens` / `temperature` / `top_p`: 默认采样参数
    - `supports_stream`: 是否支持 SSE 流式
    - `supports_multimodal`: 是否支持图片 / 视频输入
  - 键名为服务标识，值为对应的 API Key

## 重试机制

网络波动、平台限流、临时错误等都可能导致任务中断。执行过程中应遵循：

- **幂等重试**：对可重试操作（如 HTTP 请求、页面加载、API 调用）默认至少重试 3 次，间隔指数退避（1s、2s、4s、8s）。
- **区分错误类型**：
  - 网络超时 / 5xx / 临时错误 → 重试
  - 4xx / 权限不足 / 登录失效 / 账号被封 → 停下来分析，询问用户
  - captcha / 邮箱验证 / 手机验证 / 二次验证 / API 权限 → **优先询问用户**
- **保存中间状态**：每次重要操作后记录当前进度，便于中断后恢复。
- **不要无限循环**：同一操作重试 3-5 次仍失败后，切换备选方案或寻求帮助。

## 需要谨慎处理的 3 种特殊情况

在达成目标之前，原则上应持续自主尝试，只有以下 3 种情况需要特别谨慎处理。

1. **需要注册某个平台的账号并获得特定密码或权限**
   - 例如：需要注册 Reddit、Fiverr、Upwork、Gumroad、PayPal 等平台账号
   - 例如：需要获取 API Key、OAuth Token、Telegram Bot Token 等
   - **原则**：**优先询问用户**。包括平台注册、人机验证（captcha）、邮箱验证、手机验证、二次验证（2FA）、API 权限申请等所有权限类问题，都应先询问用户如何处置，由用户决定是否继续。

2. **需要用户授予或输入密码**
   - 例如：需要用户输入 Gmail、PayPal、银行、平台账号密码
   - 例如：需要用户完成 2FA、短信验证码、邮箱验证
   - **原则**：**优先询问用户**。绝不猜测密码，不尝试暴力破解。遇到此类权限问题应先询问用户，由用户决定如何处理。

3. **需要投入资金（借钱）**
   - 例如：需要花钱购买广告、域名、工具、库存、服务等
   - **必须同时告知用户这笔投入的预估 ROI（投资回报率）**
   - 必须得到用户明确同意后才能花预算

## 执行原则

- **不要按时间计费**：拒绝时薪、日薪类项目
- **避开 AI 检测**：优先选择不检测 AI 生成内容的平台或任务
- **速度优先**：在合法合规前提下，优先选择能最快产生收入的路径
- **不断尝试**：失败一个渠道后立即尝试下一个，不要长时间停顿汇报
- **持续追踪**：定期检查收入状态、流量、转化率等关键指标
- **优先使用已有资产**：先利用 `assets.product_dir` 和 `assets.history_dir` 中的已有产品和历史经验教训
- **不要泄露隐私**：SKILL 是公开文档，执行过程中获取的账号、密码、API Key、产品链接等敏感信息只保存在本地配置或密钥管理文件中，不要写回 SKILL.md
- **主动调用 find-skill**：遇到难以解决的问题或需要专业技能时，主动调用 `/find-skill` 或 `/install-skill` 寻找并安装现成的 skill 来提供帮助（例如：自动化发帖、SEO 优化、邮件营销、社媒管理等场景）

## 推荐执行策略

1. **先加载历史上下文**
   - 读取 `assets.history_dir` 下的历史记录文件，了解之前的尝试和当前状态
   - 读取 `assets.product_dir` 中的产品资料、营销文案、脚本等
   - 敏感信息从本地配置中读取，不要在日志中明文记录

2. **评估最快路径**
   - 优先尝试已有账号能直接操作的渠道
   - 如果所有自有渠道都走不通，再考虑请求用户注册新账号

3. **持续执行循环**
   - 制定 3-5 个备选方案
   - 逐个快速尝试
   - 每完成一个动作，检查是否产生收入或流量
   - 根据反馈调整策略

4. **追踪关键指标**
   - 页面浏览量（page views）
   - 销售额 / 订单数
   - 任务完成数
   - 剩余预算
   - 当前时薪是否达到速度目标

5. **达到目标或预算耗尽时停止**
   - 达到 `target.amount` 后，向用户报告最终结果和提现方式
   - 预算耗尽且无望时，向用户报告并请求下一步指示

## 汇报规则

- **不要频繁汇报**：只有在达成目标、预算耗尽、或遇到 3 种特殊情况时才停下来
- **除非遇到特殊情况，否则不要询问用户"接下来做什么"**：自己决定并执行
- **达到目标后的最终汇报需包含**：
  - 实际收入金额和货币
  - 所用时间和平均速度
  - 实际花费预算
  - 收款/提现方式
  - 可复制的方法总结

## NVIDIA integrate API 调用规范

`llm_api_keys.nvidia` 用于调用 NVIDIA integrate 提供的 OpenAI 兼容 Chat Completions 接口（例如 `minimaxai/minimax-m3` 等多模态模型）。调用时从 `config.json` 读取真实凭据，不要在代码或日志里硬编码 API Key。

引用方式示例：

```python
import json
import requests
from pathlib import Path

config = json.loads(Path(".trae/skills/make-money/config.json").read_text())
nv = config["llm_api_keys"]["nvidia"]

invoke_url = nv["invoke_url"]
api_key = nv["api_key"]
model = nv["model"]

# 流式开关：True 走 SSE，False 直接拿完整 JSON
stream = False

headers = {
    "Authorization": f"Bearer {api_key}",
    "Accept": "text/event-stream" if stream else "application/json",
}

payload = {
    "model": model,
    "messages": [{"role": "user", "content": ""}],
    "max_tokens": nv.get("max_tokens", 8192),
    "temperature": nv.get("temperature", 1.00),
    "top_p": nv.get("top_p", 0.95),
    "stream": stream,
}

# 文本请求
response = requests.post(invoke_url, headers=headers, json=payload, stream=stream)

# 多模态请求（当 supports_multimodal=True 时可用）：
# 把 messages[i]["content"] 改成 list，包含 text / image_url / video_url 三种 part：
#   {"type": "text", "text": "Describe this."}
#   {"type": "image_url", "image_url": {"url": "https://example.com/image.jpg"}}
#   {"type": "video_url", "video_url": {"url": "https://example.com/video.mp4"}}
# 也支持 data URI：{"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}

if stream:
    for line in response.iter_lines():
        if line:
            print(line.decode("utf-8"))
else:
    print(response.json())
```

### 调用约定

- **认证**：始终使用 `Authorization: Bearer $NVIDIA_API_KEY`，Key 仅来自 `config.json` 或环境变量
- **流式**：当 `supports_stream=True` 且任务需要实时输出时，启用 `stream=True` 并按 `iter_lines()` 解析
- **多模态**：当 `supports_multimodal=True` 时，`messages[].content` 可为文本或 part 列表，支持公网 URL 与 base64 data URI
- **退避**：与全 SKILL 通用重试机制一致，5xx/网络错误指数退避，401/403 停下来检查 Key
- **采样参数**：`max_tokens` / `temperature` / `top_p` 默认读 `nvidia` 段配置，可在单次调用里覆盖

## 安全与边界

- 只做合法合规的赚钱尝试
- 不利用漏洞、不刷单、不欺诈
- 不泄露用户密码或敏感信息
- 不在未经同意的情况下花钱
- 优先选择能提现到支持的收款账户的收款方式
