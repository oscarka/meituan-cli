"""
美团 MCP Server — 让 Claude / GPT 通过 Tool Calling 调用美团

架构：
  Claude/GPT
    | MCP Tool Call
    v
  mcp_server.py（本文件）
    | HTTP 调用
    v
  meituan_cli/cli.py serve（本机 18080 端口）
    | ADB + UIAutomator2
    v
  美团 App（Android 手机）

启动方式：
  # 1. 先在另一个终端启动 UI 控制服务
  python meituan_cli/cli.py serve

  # 2. 再启动 MCP Server
  python server/mcp_server.py

Claude Desktop 配置（~/.config/claude/claude_desktop_config.json）：
  {
    "mcpServers": {
      "meituan": {
        "command": "python",
        "args": ["/Users/cc/android/server/mcp_server.py"]
      }
    }
  }
"""
import sys
import json
import requests
import logging

sys.path.insert(0, __file__.replace("/server/mcp_server.py", ""))

from mcp.server.fastmcp import FastMCP

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# MCP Server 初始化
mcp = FastMCP(
    name="meituan",
    description=(
        "美团外卖 AI 驱动 — 通过 UI 自动化控制美团 App。\n"
        "标准工作流：get_state → search_restaurants → open_restaurant → get_menu → add_to_cart → view_cart → checkout"
    ),
)

# CLI Server 地址
CLI_BASE = "http://localhost:18080"


def _get(path: str, **params) -> dict:
    """调用 CLI HTTP Server（GET）"""
    try:
        r = requests.get(CLI_BASE + path, params=params, timeout=60)
        return r.json()
    except requests.exceptions.ConnectionError:
        return {
            "ok": False,
            "error": "无法连接到美团控制服务",
            "suggestion": "请先在终端运行: python meituan_cli/cli.py serve",
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _post(path: str, body: dict) -> dict:
    """调用 CLI HTTP Server（POST）"""
    try:
        r = requests.post(CLI_BASE + path, json=body, timeout=60)
        return r.json()
    except requests.exceptions.ConnectionError:
        return {
            "ok": False,
            "error": "无法连接到美团控制服务",
            "suggestion": "请先在终端运行: python meituan_cli/cli.py serve",
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ─── MCP Tools ──────────────────────────────────────────────────────────────

@mcp.tool()
def get_state() -> str:
    """
    获取当前美团 App 的状态。
    返回 page（当前页面类型）、activity（Android Activity 名）、screen_texts（屏幕文字摘要）。
    page 枚举：home / search_input / search_results / restaurant_menu / cart / checkout / order / meituan_other / unknown

    每次执行操作后都应调用此工具确认状态变化。
    """
    result = _get("/state")
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
def get_screen() -> str:
    """
    获取当前屏幕所有 UI 元素（文字、坐标、是否可点击）。
    用于调试，或在 get_state 信息不足时使用。
    """
    result = _get("/screen")
    if result.get("ok"):
        elements = result.get("elements", [])
        # 只返回有文字的元素，避免数据过多
        visible = [e for e in elements if e.get("text") or e.get("desc")]
        return json.dumps({"ok": True, "elements": visible, "count": len(visible)},
                          ensure_ascii=False, indent=2)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
def launch_app() -> str:
    """
    启动美团 App（如果未运行或不在前台）。
    执行后等待 3 秒让 App 加载完成。
    """
    result = _get("/launch")
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
def search_restaurants(keyword: str) -> str:
    """
    在美团搜索餐厅或菜品。

    Args:
        keyword: 搜索关键词，例如"肯德基"、"汉堡"、"麻辣烫"

    返回餐厅列表，包含序号（_card_idx 或列表位置）、名字、评分、配送时间等。
    搜索成功后，用 open_restaurant(target=0) 进入第一家。

    注意：如果遇到验证码提示，需要用户手动在手机上完成验证。
    """
    result = _get("/search", keyword=keyword)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
def open_restaurant(target: str) -> str:
    """
    进入一家餐厅。

    Args:
        target: 餐厅序号（数字字符串，如 "0" 表示第一家）或餐厅名称

    通常在 search_restaurants 后调用，传入结果列表的序号。
    成功后会返回当前页面状态（应变为 restaurant_menu）。
    """
    result = _get("/open", target=target)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
def get_menu() -> str:
    """
    获取当前餐厅的菜单。

    需要先调用 open_restaurant 进入餐厅。
    返回菜品列表，包含名称（name）和价格（price）。
    加购物车时使用 name 字段作为参数。
    """
    result = _get("/menu")
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
def add_to_cart(item_name: str) -> str:
    """
    将菜品加入购物车。

    Args:
        item_name: 菜品名称，必须与 get_menu 返回的 name 字段一致（可以是子串）

    需要先调用 get_menu 获取菜品列表，再调用此接口。
    """
    result = _post("/add_to_cart", {"item": item_name})
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
def view_cart() -> str:
    """
    查看购物车内容，返回已选菜品列表和总价。
    确认无误后调用 checkout 去结算。
    """
    result = _get("/cart")
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
def checkout() -> str:
    """
    进入结算页面（停在确认订单页，不会自动付款）。
    需要用户在手机上手动确认并支付。

    安全保证：本工具永远不会自动付款。
    """
    result = _get("/checkout")
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
def tap_element(keyword: str) -> str:
    """
    点击屏幕上包含指定文字的元素。

    Args:
        keyword: 要点击的元素文字（支持部分匹配）

    当标准业务流无法完成操作时使用（如关闭弹窗、点击特殊按钮）。
    """
    result = _get("/tap", keyword=keyword)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
def input_text(text: str) -> str:
    """
    在当前输入框中输入文字（支持中文）。

    Args:
        text: 要输入的文字
    """
    result = _get("/type", text=text)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
def swipe_screen(direction: str = "up", distance: int = 500) -> str:
    """
    滑动屏幕，用于滚动查看更多内容。

    Args:
        direction: 滑动方向，up/down/left/right
        distance: 滑动距离（像素），默认 500
    """
    result = _get("/swipe", direction=direction, distance=distance)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
def press_back() -> str:
    """
    按返回键，返回上一个页面。
    """
    result = _get("/back")
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
def wait_for_element(keyword: str, timeout: int = 10) -> str:
    """
    等待屏幕上出现包含指定文字的元素。

    Args:
        keyword: 等待出现的文字
        timeout: 超时时间（秒），默认 10

    用于在操作后等待页面加载完成。
    """
    result = _get("/wait", keyword=keyword, timeout=timeout)
    return json.dumps(result, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    print("启动美团 MCP Server...")
    print(f"依赖服务：{CLI_BASE}（请确保已运行 python meituan_cli/cli.py serve）")
    mcp.run()
