# meituan-cli 🍜

> **把物理世界的美团 App 变成大模型可调用的 API 工具**
> 基于 UIAutomator2 + ADB 直接视觉控制，零抓包、防封禁，专为 AI Agent（ClawBot, Claude, GPT）打造的纯正“机械臂”。

## ✨ 核心特性突破 (v2.0)

1. **防封禁设计**：不走任何 HTTP 抓包，不需要逆向协议，纯模拟真人点击滑动。
2. **动态视觉雷达**：彻底抛弃死板的坐标点击！针对瑞幸咖啡、麦当劳等复杂的店铺 UI（几百字的商品描述导致加购按钮被严重挤压），自研基于 Y 轴坐标聚类的“视觉就近寻址”算法，精准锁定最近的 `+`、`选规格` 或 `选套餐` 按钮。
3. **多级规格自适应**：智能感知二级弹窗（如温度、甜度、杯型），自动点击默认项并处理烦人的强制残留弹窗。
4. **业务流拦截**：精准拦截并反馈“差 ¥7 起送”、“未点必选品”等复杂业务异常，并将具体的错误原因返回给大模型。

---

## 架构

```
Claude / Kimi / 任意 Agent
        │
        │ HTTP JSON API (Skill 调用)
        ▼
   cli.py serve（HTTP 控制服务 :18080）
        │
        │ UIAutomator2 + ADB (模拟点击)
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
- 手机开启 USB 调试并连接（需解锁亮屏）
- 美团 App 已安装并登录

### 安装依赖

```bash
pip install -r requirements.txt
python -m uiautomator2 init   # 首次运行需要
```

### 启动服务

```bash
# 启动 HTTP Server（供 AI 调用）
python cli.py serve --port 18080

# 或者直接命令行验证
python cli.py search "麻辣烫"
python cli.py open 0
python cli.py waimai
python cli.py menu
python cli.py add "招牌麻辣烫"
python cli.py checkout
```

---

## 🤖 AI Agent 深度体验：Kimi 端到端点单

我们提供了一个内置的演示脚本 `simulate_agent.py`，可以直接使用 Moonshot Kimi 大模型体验无人值守点餐流程：

```bash
# 确保启动了 cli server 后，运行体验脚本
python simulate_agent.py
```
*大模型将会自动规划路径：搜索店铺 -> 进入店铺 -> 切换外卖 -> 店内搜索 -> 加购 -> 去结算。*

> **如何将本工具发布为大模型平台（如 Coze/Dify/FastGPT）的公共技能？**
> 请查阅项目内附带的 [SkillHub_Publish_Guide.md](SkillHub_Publish_Guide.md) 指南。内含完整的 OpenAPI Schema 和使用建议。

---

## HTTP API 完整列表

### 核心业务 (AI Agent 推荐使用)

| 接口 | 说明 | 返回字段 |
|------|------|---------|
| `GET /search?keyword=XX` | 搜索餐厅 | `restaurants[], count` |
| `GET /open?target=0` | 进入餐厅（序号或店名） | `ok, current_page` |
| `GET /tap?keyword=外卖` | 进入外卖点菜页 | `ok, message` |
| `GET /type?text=XX` | 店内搜索某款菜品 | `ok, typed` |
| `POST /add_to_cart` body: `{"item":"XX"}` | 智能加购物车 (处理弹窗) | `ok, cart_total, cart_count` |
| `GET /cart` | 查看购物车 | `items[], total, count` |
| `GET /checkout` | 去结算 | `ok, address, total, delivery_time` |

### 底层控制

| 接口 | 说明 |
|------|------|
| `GET /screen` | 当前屏幕所有 UI 元素 |
| `GET /tap?keyword=XX` | 点击含关键字的元素 |
| `POST /tap_xy` body: `{"x":0,"y":0}` | 按坐标点击 |
| `GET /swipe?direction=up` | 滑动（up/down/left/right） |
| `GET /back` | 返回键 |
| `GET /home` | Home 键 |
| `GET /launch` | 启动/唤醒美团 |

所有响应格式：
```json
{ "ok": true,  ...data }
{ "ok": false, "error": "未达到起送金额，还差 ¥7", "suggestion": "继续调用 /add_to_cart 加菜..." }
```

---

## 文件结构

```
meituan-cli/
├── cli.py                    # CLI 入口 + HTTP Server (暴露 API)
├── meituan.py                # 美团核心业务逻辑（视觉雷达寻址/购物车/结算分析）
├── device.py                 # 设备底层控制封装（基于 U2）
├── simulate_agent.py         # ClawBot & Kimi 大模型联动演示脚本
├── SkillHub_Publish_Guide.md # 第三方大模型平台 Skill 发布指南
├── server/
│   └── mcp_server.py         # MCP Server（供 Claude 接入）
├── requirements.txt
└── README.md
```

---

## ⚠️ 注意事项与声明

- **安全红线**：`checkout` 接口**永远不会自动付款**，所有点单流转最终均会安全地停留在美团官方的“确认订单/支付”页面，需要用户通过指纹或密码亲自付款。
- **环境要求**：由于纯视觉驱动，高频操作可能会触发平台的真机滑块验证，目前版本如果遇到滑块会抛出 error，需人在屏幕上滑动一下解锁。
- **网络需求**：AI 需与运行此代码的电脑在同一局域网（或通过公网映射）方可通信。

## License

MIT
