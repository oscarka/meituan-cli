# 🚀 技能发布指南：将 Meituan AI CLI 上传至 SkillHub

本指南将指导你如何将 **Meituan AI CLI** 封装为一个标准的 AI Agent Skill，并发布到 [SkillHub] (或其他如 Coze、Dify、FastGPT 等大模型编排平台)，让所有的 AI 助理（如 ClawBot、GPT-4o、Claude 3.5）都能直接调用该技能进行物理世界的外卖点餐！

---

## 1. 核心概念与工作流

向大模型开放此技能时，必须在 Skill 的系统提示词或说明中明确交代**外卖点餐的严谨步骤**。请在你的 Agent Platform（SkillHub）的“系统提示词（System Prompt）”或“技能描述”中填入以下说明：

### 🤖 推荐使用的 Agent System Prompt
```markdown
你现在绑定了“美团外卖物理点餐” Skill。你可以通过这套能力直接控制真机进行点菜。为了确保点单成功，你必须**严格遵循**以下 6 步外卖点单工作流：

1. 调用 `meituan_search` 搜索餐厅。
2. 根据返回的列表，调用 `meituan_open` 进入目标餐厅。
3. 调用 `meituan_waimai` 切换到“外卖”点菜页（注意：必须执行此步才能看到加购按钮）。
4. 调用 `meituan_search_in_store` 在店内搜索特定的菜品名。
5. 调用 `meituan_add_to_cart` 将该菜品加入购物车（遇到多规格弹窗，底层会自动处理）。
6. 调用 `meituan_checkout` 去结算（此操作只跳转到支付页，不会自动扣款）。

⚠️ 注意事项：
- 每次调用后，请根据返回结果决定下一步操作，切勿跳跃执行。
- 只有返回 `{"ok": true}` 才代表该步骤成功。如果返回 `error`，请查看 `suggestion` 字段并尝试重试或修改策略。
```

---

## 2. API Schema / OpenAPI 规范 (SkillHub 导入配置)

大部分 SkillHub 平台支持直接导入 OpenAPI (Swagger) JSON/YAML。以下是你需要填入平台的 Schema 定义。这 6 个核心工具组成了无懈可击的外卖闭环。

```json
{
  "openapi": "3.1.0",
  "info": {
    "title": "Meituan Delivery Automation API",
    "description": "物理驱动美团 App 进行端到端的外卖搜索、加购与结算。",
    "version": "v1.0.0"
  },
  "servers": [
    {
      "url": "http://<YOUR_LOCAL_IP>:18080",
      "description": "本地 Android 手机网关 (需内网穿透或局域网调用)"
    }
  ],
  "paths": {
    "/search": {
      "get": {
        "operationId": "meituan_search",
        "summary": "搜索外卖餐厅",
        "description": "在美团外卖频道搜索指定的餐厅或菜品名，返回附近的店铺列表及索引号。",
        "parameters": [
          {
            "name": "keyword",
            "in": "query",
            "required": true,
            "description": "要搜索的餐厅名或菜名 (如 '瑞幸咖啡')",
            "schema": { "type": "string" }
          }
        ]
      }
    },
    "/open": {
      "get": {
        "operationId": "meituan_open",
        "summary": "进入餐厅",
        "description": "根据 /search 接口返回的列表，指定 target 序号进入某家店。",
        "parameters": [
          {
            "name": "target",
            "in": "query",
            "required": true,
            "description": "目标餐厅的索引序号 (如 0 代表第一家)",
            "schema": { "type": "integer" }
          }
        ]
      }
    },
    "/tap": {
      "get": {
        "operationId": "meituan_waimai",
        "summary": "切换到外卖点菜页",
        "description": "在店铺主页点击「外卖」选项卡。必须在进店后立即调用以确保在点菜模式。",
        "parameters": [
          {
            "name": "keyword",
            "in": "query",
            "required": true,
            "description": "必须填入 '外卖'",
            "schema": { "type": "string", "enum": ["外卖"] }
          }
        ]
      }
    },
    "/type": {
      "get": {
        "operationId": "meituan_search_in_store",
        "summary": "在店铺内搜索菜品",
        "description": "在当前店铺的搜索框内输入菜品名字。调用前建议先通过 /tap?keyword=搜索 激活搜索框。",
        "parameters": [
          {
            "name": "text",
            "in": "query",
            "required": true,
            "description": "要搜索的具体菜品名称",
            "schema": { "type": "string" }
          }
        ]
      }
    },
    "/add_to_cart": {
      "post": {
        "operationId": "meituan_add_to_cart",
        "summary": "将菜品加入购物车",
        "description": "使用智能视觉雷达扫描屏幕，识别菜品名称附近的 '+' 或 '选规格' 按钮，自动处理多规格弹窗并加入购物车。",
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "properties": {
                  "item": {
                    "type": "string",
                    "description": "屏幕上可见的准确菜品名称"
                  }
                },
                "required": ["item"]
              }
            }
          }
        }
      }
    },
    "/checkout": {
      "get": {
        "operationId": "meituan_checkout",
        "summary": "去结算",
        "description": "点击购物车结算按钮。自动校验起送价、必选品等业务限制。安全接口，仅停留在确认订单页，绝不会自动扣款付款。",
        "parameters": []
      }
    }
  }
}
```

---

## 3. 发布亮点 (Skill 营销文案)

在 SkillHub 发布时，你需要一段抓人眼球的简介。你可以直接使用以下文案：

**🔥 技能名称**： 美团外卖物理外挂 (Meituan Physical Automation)
**💡 一句话简介**： 让 AI 拥有在物理世界点外卖的双手！完全模拟真人滑动、点击，智能处理规格选择与起送价限制。
**✨ 核心特性**：
- 🛡️ **非逆向、防封禁**：不走抓包，不调内部接口，纯粹基于 Accessibility/UIAutomator 视觉驱动，和真人操作毫无二致。
- 🧠 **动态雷达寻址**：突破死板坐标限制！动态感知“商品描述”长度，精准打击偏离原位的“选规格”、“选套餐”按钮。
- 🤖 **复杂场景自适应**：自动处理星巴克、瑞幸等多级规格（冰度、糖度）弹窗，自动识别并清理遗留 Modal。
- ⛔ **安全第一**：最终步骤强制停留在**支付页**，资金绝对安全，由你本人按下支付指纹！

## 4. 给开发者的建议 (注意事项)

在你的项目介绍页，提醒下载使用该技能的用户：
1. 本地需要运行 `python cli.py serve --port 18080` 服务，且手机通过 USB 或无线 ADB 保持连接。
2. 如果你的 SkillHub 运行在云端（如 Coze 云服务），你可能需要通过 **ngrok / cpolar / Serverless Gateway** 等内网穿透工具，将你本地电脑的 `18080` 端口暴露到公网，然后在 Schema 的 `servers.url` 中填入公网地址。
3. 演示脚本 `simulate_agent.py` 已包含在仓库中，小白用户可以通过该脚本快速体验大模型驱动本地手机的快感。
