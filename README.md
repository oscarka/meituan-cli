# meituan-cli 🍜

> **把美团 App 变成 AI 可调用的 HTTP API**
> 基于 UIAutomator2 + ADB 直接控制 UI，无需逆向，数据结构化回流给 AI Agent。

## 架构

```
Claude / GPT / 任意 AI Agent
        │
        │ HTTP JSON API
        ▼
  cli.py serve（HTTP 控制服务 :7788）
        │
        │ UIAutomator2 + ADB
        ▼
  美团 App（Android 手机/模拟器）
```

也支持通过 MCP 接入 Claude Desktop：

```
Claude Desktop ──MCP──► server/mcp_server.py ──HTTP──► cli.py serve
```

---

## 快速开始

### 环境要求

- Python 3.9+
- ADB 已安装（`brew install android-platform-tools`）
- 手机开启 USB 调试并连接
- 美团 App 已安装并登录

### 安装依赖

```bash
pip install -r requirements.txt
python -m uiautomator2 init   # 首次运行需要
```

### 启动

```bash
# 启动 HTTP Server（AI 调用模式）
python cli.py serve --port 7788

# 或者直接命令行调用
python cli.py search "麻辣烫"
python cli.py open 0
python cli.py waimai
python cli.py menu
python cli.py add "香辣鸡腿堡"
python cli.py cart
python cli.py checkout
```

---

## 标准外卖工作流

```
GET /search?keyword=麻辣烫    → 搜索餐厅
GET /open?target=0            → 进入第一家
GET /waimai                   → 跳转外卖点菜页
GET /menu                     → 获取菜单
GET /add_to_cart?item=XX      → 加购物车
GET /cart                     → 查看购物车
GET /checkout                 → 去结算（不自动付款）
GET /address                  → 查看收货地址
```

---

## HTTP API 完整列表

### 核心业务

| 接口 | 说明 | 返回字段 |
|------|------|---------|
| `GET /state` | 当前页面状态 | `page, activity, screen_texts` |
| `GET /search?keyword=XX` | 搜索餐厅 | `restaurants[], count` |
| `GET /open?target=0` | 进入餐厅（序号或店名） | `ok, current_page` |
| `GET /waimai` | 进入外卖点菜页 | `ok, message` |
| `GET /menu` | 获取外卖菜单 | `menu[{name,price}], count` |
| `GET /add_to_cart?item=XX` | 加购物车 | `ok, cart_total, cart_count` |
| `POST /add_to_cart` body: `{"item":"XX"}` | 加购（POST） | 同上 |
| `GET /cart` | 查看购物车 | `items[], total, count` |
| `GET /checkout` | 去结算 | `ok, address, total, delivery_time` |
| `GET /address` | 查看收货地址 | `address, name, phone` |
| `GET /food_channel?screens=4` | 浏览附近推荐餐厅 | `restaurants[], count` |

### 底层控制

| 接口 | 说明 |
|------|------|
| `GET /screen` | 当前屏幕所有 UI 元素 |
| `GET /tap?keyword=XX` | 点击含关键字的元素 |
| `POST /tap_xy` body: `{"x":0,"y":0}` | 按坐标点击 |
| `GET /type?text=XX` | 输入文字 |
| `GET /swipe?direction=up` | 滑动（up/down/left/right） |
| `GET /back` | 返回键 |
| `GET /home` | Home 键 |
| `GET /launch` | 启动/唤醒美团 |
| `GET /wait?keyword=XX&timeout=10` | 等待元素出现 |

所有响应格式：
```json
{ "ok": true,  ...data }
{ "ok": false, "error": "...", "suggestion": "..." }
```

---

## 给 AI 的 System Prompt

见 [`AGENT_PROMPT.md`](AGENT_PROMPT.md) —— 可直接作为 Claude/GPT 的 system prompt 使用。

---

## MCP 接入 Claude Desktop

**1. 启动控制服务：**
```bash
python cli.py serve --port 7788
```

**2. 启动 MCP Server：**
```bash
python server/mcp_server.py
```

**3. Claude Desktop 配置** (`~/.config/claude/claude_desktop_config.json`)：
```json
{
  "mcpServers": {
    "meituan": {
      "command": "python",
      "args": ["/path/to/meituan-cli/server/mcp_server.py"]
    }
  }
}
```

---

## 文件结构

```
meituan-cli/
├── cli.py              # CLI 入口 + HTTP Server
├── meituan.py          # 美团业务逻辑（搜索/进店/菜单/购物车/结算）
├── device.py           # 设备底层控制（ADB + UIAutomator2 原子操作）
├── captcha_bypass.js   # 验证码绕过（Frida，实验性）
├── server/
│   └── mcp_server.py   # MCP Server（Claude Desktop 接入）
├── AGENT_PROMPT.md     # AI 使用手册（System Prompt）
├── requirements.txt
└── README.md
```

---

## 注意事项

- `checkout` **永远不会自动付款**，仅跳转到确认页
- 高频操作可能触发验证码，需手动在手机上滑动解锁
- 需保持手机 USB 连接 + USB 调试开启
- 中文搜索依赖 ADB Broadcast 输入，无需安装特殊输入法

## License

MIT
