import os
import re
import requests
import socket
from openai import OpenAI
from tavily import TavilyClient
from datetime import datetime
from pywebio import start_server
from pywebio.input import textarea
from pywebio.output import put_markdown, put_loading, put_text

# ==================== 1. 系统提示词 ====================
AGENT_SYSTEM_PROMPT = """
你是一个智能旅行助手。你的任务是分析用户的请求，并使用可用工具一步步地解决问题。
- 如果用户输入中已经包含了城市名称（如"南京"）、时间、预算等信息，即使表达很简短，也应该直接使用这些信息调用工具，不要要求用户重复提供。

# 可用工具:
- `get_weather(city: str)`: 查询指定城市的实时天气。
- `get_attraction(city: str, weather: str)`: 根据城市和天气搜索推荐的旅游景点。
- `book_hotel(city: str, budget: str)`: 根据城市和预算模拟预订酒店。
- `get_news(city: str)`: 搜索指定城市最近的旅游相关新闻（活动、节日、天气预警等）。
- `get_current_datetime()`: 查询当前真实的日期和时间（年份、月份、日期、小时、分钟）。

# 输出格式要求:
你的每次回复必须严格遵循以下格式，包含一对Thought和Action：

Thought: [你的思考过程和下一步计划]
Action: [你要执行的具体行动]

Action的格式必须是以下之一：
1. 调用工具：function_name(arg_name="arg_value")
2. 结束任务：Finish[最终答案]

# 重要提示:
- 每次只输出一对Thought-Action
- Action必须在同一行，不要换行
- 当收集到足够信息可以回答用户问题时，必须使用 Action: Finish[最终答案] 格式结束
- 如果用户输入中已包含城市、时间、预算等信息，即使表达简短，也直接使用这些信息调用工具，不要反问用户重复提供
- 酒店工具返回的是真实数据，回答时绝对不要使用"模拟"这个词，直接说"为您找到以下酒店"

请开始吧！
"""

# ==================== 2. 工具函数 ====================
def get_weather(city: str) -> str:
    """通过 wttr.in 查询实时天气"""
    url = f"https://wttr.in/{city}?format=j1"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        current = data['current_condition'][0]
        weather_desc = current['weatherDesc'][0]['value']
        temp_c = current['temp_C']
        return f"{city}当前天气:{weather_desc}，气温{temp_c}摄氏度"
    except requests.exceptions.RequestException as e:
        return f"错误:查询天气时遇到网络问题 - {e}"
    except (KeyError, IndexError) as e:
        return f"错误:解析天气数据失败，可能是城市名称无效 - {e}"

def get_attraction(city: str, weather: str) -> str:
    """使用 Tavily Search API 搜索景点推荐"""
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        return "错误:未配置TAVILY_API_KEY环境变量。"

    tavily = TavilyClient(api_key=api_key)
    query = f"'{city}' 在'{weather}'天气下最值得去的旅游景点推荐及理由"

    try:
        response = tavily.search(query=query, search_depth="basic", include_answer=True)
        if response.get("answer"):
            return response["answer"]
        formatted = []
        for result in response.get("results", []):
            formatted.append(f"- {result['title']}: {result['content']}")
        if not formatted:
            return "抱歉，没有找到相关的旅游景点推荐。"
        return "根据搜索，为您找到以下信息:\n" + "\n".join(formatted)
    except Exception as e:
        return f"错误:执行Tavily搜索时出现问题 - {e}"

# ==================== 酒店 API 接口说明 ====================
# 当前状态：SerpApi Google Hotels 真实接口
# 降级策略：API 失败时自动回退到模拟数据
# 接入方式：设置环境变量 REAL_HOTEL_API_KEY
# ==========================================================

def book_hotel(city: str, budget: str) -> str:
    """酒店预订工具（SerpApi 真实接口 + Fallback 降级）"""
    real_api_key = os.environ.get("REAL_HOTEL_API_KEY")
    if real_api_key:
        try:
            from serpapi import GoogleSearch
            from datetime import datetime, timedelta

            sort_map = {"低": "3", "中": "8", "高": "8"}
            sort_by = sort_map.get(budget, "8")

            today = datetime.now().strftime("%Y-%m-%d")
            tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

            params = {
                "engine": "google_hotels",
                "q": f"{city} hotel",
                "gl": "cn",
                "hl": "zh-cn",
                "currency": "CNY",
                "sort_by": sort_by,
                "check_in_date": today,
                "check_out_date": tomorrow,
                "adults": "2",
                "api_key": real_api_key
            }

            search = GoogleSearch(params)
            results = search.get_dict()
            hotels = results.get("properties", [])[:3]

            if hotels:
                hotel_list = []
                for h in hotels:
                    name = h.get("name", "未知酒店")
                    rate = h.get("rates_per_night", {})
                    if isinstance(rate, dict):
                            lowest = rate.get("lowest") or rate.get("price") or "暂无"
                            currency = rate.get("currency", "¥")
                    elif isinstance(rate, str):
                            lowest = rate
                            currency = "¥"
                    else:
                            lowest = "暂无"
                            currency = "¥"
                    hotel_list.append(f"- {name}: {currency}{lowest}/晚")
                return f"🏨 在{city}为您找到以下真实酒店:\n" + "\n".join(hotel_list)

            print("[酒店API] 未找到酒店结果，降级到模拟数据")

        except Exception as e:
            print(f"[酒店API] 调用失败，降级到模拟数据: {e}")

    # Fallback
    budget_map = {
        "低": f"🏨 已为您在{city}预订经济型快捷酒店，约200元/晚。（注：当前为模拟数据，接入真实API后可返回实时价格）",
        "中": f"🏨 已为您在{city}预订舒适型商务酒店，约500元/晚。（注：当前为模拟数据，接入真实API后可返回实时价格）",
        "高": f"🏨 已为您在{city}预订豪华五星级酒店，约1500元/晚。（注：当前为模拟数据，接入真实API后可返回实时价格）"
    }
    return budget_map.get(budget, budget_map["中"])

def get_news(city: str) -> str:
    """使用 Tavily 搜索指定城市最近的旅游新闻"""
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        return "错误:未配置TAVILY_API_KEY环境变量。"

    tavily = TavilyClient(api_key=api_key)
    query = f"{city} 旅游 新闻 最近 活动 天气预警"

    try:
        response = tavily.search(query=query, search_depth="basic", include_answer=False)
        results = response.get("results", [])
        if not results:
            return f"未找到关于{city}的最近旅游新闻。"

        news_list = []
        for item in results[:3]:
            news_list.append(f"- {item['title']}: {item['content']}")
        return f"关于{city}的最新旅游相关新闻:\n" + "\n".join(news_list)
    except Exception as e:
        return f"错误:搜索新闻失败 - {e}"

def get_current_datetime() -> str:
    """返回当前精确的日期和时间"""
    now = datetime.now()
    return f"现在是{now.year}年{now.month}月{now.day}日，{now.hour}时{now.minute}分（系统本地时间）。"

# 工具字典
available_tools = {
    "get_weather": get_weather,
    "get_attraction": get_attraction,
    "book_hotel": book_hotel,
    "get_news": get_news,
    "get_current_datetime": get_current_datetime, 
}

# ==================== 3. 大模型客户端 ====================
class OpenAICompatibleClient:
    def __init__(self, model: str, api_key: str, base_url: str):
        self.model = model
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def generate(self, prompt: str, system_prompt: str) -> str:
        print("正在调用大语言模型...")
        try:
            messages = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': prompt}
            ]
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=False
            )
            answer = response.choices[0].message.content
            print("大语言模型响应成功。")
            return answer
        except Exception as e:
            print(f"调用LLM API时发生错误: {e}")
            return "错误:调用语言模型服务时出错。"

# ==================== 4. 封装 Agent 逻辑 ====================
def run_agent(user_message, history=None):
    """接收用户输入字符串，返回智能体的最终回复。"""
    llm = OpenAICompatibleClient(
        model="deepseek-chat",
        api_key=os.environ["DEEPSEEK_API_KEY"],
        base_url="https://api.deepseek.com"
    )
    if history is None:
        history = []
    history.append(f"用户请求: {user_message}")
    prompt_history = history

    for i in range(5):
        full_prompt = "\n".join(prompt_history)
        llm_output = llm.generate(full_prompt, AGENT_SYSTEM_PROMPT)

        # 截断多余的 Thought-Action
        match = re.search(r'(Thought:.*?Action:.*?)(?=\n\s*(?:Thought:|Action:|Observation:)|\Z)', llm_output, re.DOTALL)
        if match:
            truncated = match.group(1).strip()
            if truncated != llm_output.strip():
                llm_output = truncated
        prompt_history.append(llm_output)

        action_match = re.search(r"Action: (.*)", llm_output, re.DOTALL)
        if not action_match:
            prompt_history.append("Observation: 错误: 无法解析 Action")
            continue

        action_str = action_match.group(1).strip()
        if action_str.startswith("Finish"):
            finish_match = re.match(r"Finish\[(.*)\]", action_str, re.DOTALL)
            if finish_match:
                final_answer = finish_match.group(1).strip()
            else:
                final_answer = action_str.replace("Finish", "").strip("[]: ").strip()
            return final_answer

        tool_match = re.search(r"(\w+)\(([^)]*)\)", action_str)
        if not tool_match:
            prompt_history.append(f"Observation: 错误: 无法解析工具调用 - {action_str}")
            continue

        tool_name = tool_match.group(1)
        args_str = tool_match.group(2)
        kwargs = dict(re.findall(r'(\w+)="([^"]*)"', args_str))

        if tool_name in available_tools:
            observation = available_tools[tool_name](**kwargs)
        else:
            observation = f"错误:未定义的工具 '{tool_name}'"
        prompt_history.append(f"Observation: {observation}")

    return "抱歉，我暂时无法完成您的请求，请稍后再试。"

# ==================== 5. 配置密钥（改成你自己的） ====================
from config import DEEPSEEK_API_KEY, TAVILY_API_KEY,REAL_HOTEL_API_KEY
os.environ["DEEPSEEK_API_KEY"] = DEEPSEEK_API_KEY
os.environ["TAVILY_API_KEY"] = TAVILY_API_KEY
os.environ["REAL_HOTEL_API_KEY"] = REAL_HOTEL_API_KEY
#os.environ["REAL_HOTEL_API_KEY"] = "你的SerpApi密钥"

def main():
    """PyWebIO 主界面：循环接收用户输入，显示助手回复"""
    put_markdown("# 🌈 智能旅行助手")
    put_markdown("我是您的私人旅行管家，可以帮您查天气、推荐景点、预订酒店、查找最新旅游新闻。")
    put_markdown("---")
    chat_history = []
    while True:
        user_input = textarea("请输入您的旅行需求（输入 exit 退出）", rows=3,
                              placeholder="例如：最近北京有什么大事？会影响旅游吗？")
        if user_input.strip().lower() == 'exit':
            chat_history.clear() 
            put_text("再见！")
            break
         # 清理输入中的多余换行，避免影响模型解析
        cleaned_input = " ".join(user_input.strip().splitlines())
        put_markdown(f"**🧑 你**：{cleaned_input}")
        with put_loading('border', 'primary'):
            reply = run_agent(cleaned_input, chat_history)
            chat_history.append(f"助手回答: {reply}")
        put_markdown(f"**🤖 助手**：{reply}")
        put_markdown("---")

if __name__ == "__main__":
    # 自动寻找空闲端口，避免冲突
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('', 0))
    port = sock.getsockname()[1]
    sock.close()
    print(f'🚀 服务已启动，请打开 http://localhost:{port}')
    start_server(main, port=port, debug=True, cdn=False, css_style="""
    body {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%) !important;
        min-height: 100vh;
    }
    """)
