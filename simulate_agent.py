import os
import time
import json
import requests
from openai import OpenAI
import subprocess

# 配置 OpenRouter (请设置环境变量 OPENROUTER_API_KEY)
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "sk-or-v1-...")
# Kimi 的模型名在 OpenRouter 上是 moonshotai/kimi-k2.6
MODEL_NAME = "moonshotai/kimi-k2.6"

BASE_URL = "http://127.0.0.1:18080"

# 定义 Clawbot 可以使用的 Tool
tools = [
    {
        "type": "function",
        "function": {
            "name": "meituan_search",
            "description": "搜索美团外卖餐厅",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {"type": "string", "description": "要搜索的餐厅名或菜名"}
                },
                "required": ["keyword"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "meituan_open",
            "description": "进入搜索列表中的某家餐厅",
            "parameters": {
                "type": "object",
                "properties": {
                    "target": {"type": "integer", "description": "要进入的餐厅序号（从 0 开始）"}
                },
                "required": ["target"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "meituan_waimai",
            "description": "在店铺内点击「外卖」选项卡（确保处于外卖模式）",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "meituan_search_in_store",
            "description": "在当前店铺内搜索某个特定菜品（如果菜品太多找不到时使用）",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {"type": "string", "description": "要搜索的菜品名称"}
                },
                "required": ["keyword"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "meituan_add_to_cart",
            "description": "在当前屏幕可见的情况下，将菜品加入购物车",
            "parameters": {
                "type": "object",
                "properties": {
                    "item": {"type": "string", "description": "菜品准确名称"}
                },
                "required": ["item"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "meituan_checkout",
            "description": "去结算（不会自动付款）",
            "parameters": {"type": "object", "properties": {}}
        }
    }
]

def execute_tool(name, args):
    print(f"\n[Agent Tool Call] {name}({args})")
    try:
        if name == "meituan_search":
            res = requests.get(f"{BASE_URL}/search", params={"keyword": args["keyword"]})
        elif name == "meituan_open":
            res = requests.get(f"{BASE_URL}/open", params={"target": args["target"]})
        elif name == "meituan_waimai":
            res = requests.get(f"{BASE_URL}/tap", params={"keyword": "外卖"})
        elif name == "meituan_search_in_store":
            requests.get(f"{BASE_URL}/tap", params={"keyword": "搜索"})
            time.sleep(1)
            res = requests.get(f"{BASE_URL}/type", params={"text": args["keyword"]})
            time.sleep(1)
        elif name == "meituan_add_to_cart":
            res = requests.post(f"{BASE_URL}/add_to_cart", json={"item": args["item"]})
        elif name == "meituan_checkout":
            res = requests.get(f"{BASE_URL}/checkout")
        else:
            return json.dumps({"error": f"Unknown tool: {name}"})
        
        data = res.json()
        print(f"[Tool Response] {json.dumps(data, ensure_ascii=False)}")
        return json.dumps(data, ensure_ascii=False)
    except Exception as e:
        print(f"[Tool Error] {e}")
        return json.dumps({"error": str(e)})

def run_agent():
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
    )
    
    messages = [
        {"role": "system", "content": "你是 ClawBot，一个智能语音/文字助理。你现在绑定了美团外卖点餐的 Skill。你需要遵循以下严格的点单工作流：1. 调用 meituan_search 搜索餐厅。2. 调用 meituan_open 进入餐厅。3. 调用 meituan_waimai 切换到外卖点菜页。4. 调用 meituan_search_in_store 搜索具体菜品名。5. 调用 meituan_add_to_cart 加购该菜品。6. 调用 meituan_checkout 去结算。每次调用工具后，根据返回结果决定下一步操作，必须一步步执行，直到成功进入结算页。"},
        {"role": "user", "content": "帮我点一杯瑞幸咖啡的生椰拿铁，选第一家店就行。"}
    ]
    
    print("======== ClawBot Agent Started ========")
    print("User: 帮我点一杯瑞幸咖啡的生椰拿铁，选第一家店就行。\n")
    
    while True:
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                tools=tools,
                tool_choice="auto",
            )
        except Exception as e:
            print("API Error:", e)
            break
            
        message = response.choices[0].message
        messages.append(message)
        
        if message.content:
            print(f"[ClawBot] {message.content}\n")
            
        if not message.tool_calls:
            # 如果没有工具调用，说明任务完成或需要用户回复
            break
            
        for tool_call in message.tool_calls:
            args = json.loads(tool_call.function.arguments)
            result = execute_tool(tool_call.function.name, args)
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": tool_call.function.name,
                "content": result
            })

if __name__ == "__main__":
    # Ensure app is killed and fresh start
    os.system("adb shell am force-stop com.sankuai.meituan")
    
    # 启动 cli server 在后台
    print("启动 meituan-cli server...")
    server = subprocess.Popen(["python", "cli.py", "serve"])
    time.sleep(3) # wait for server to bind port
    
    try:
        # 首先让 App 回到首页
        print("初始化美团 App...")
        requests.get(f"{BASE_URL}/launch")
        time.sleep(4)
        
        run_agent()
    finally:
        server.terminate()
        print("Server terminated.")
