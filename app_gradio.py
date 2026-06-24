import os
import re
import requests
import socket
from openai import OpenAI
from tavily import TavilyClient
from datetime import datetime, timedelta
from config import DEEPSEEK_API_KEY, TAVILY_API_KEY, REAL_HOTEL_API_KEY
import gradio as gr

os.environ["DEEPSEEK_API_KEY"] = DEEPSEEK_API_KEY
os.environ["TAVILY_API_KEY"] = TAVILY_API_KEY
os.environ["REAL_HOTEL_API_KEY"] = REAL_HOTEL_API_KEY

# ==================== 系统提示词 ====================
AGENT_SYSTEM_PROMPT = """
你是一个智能旅行助手。分析用户请求，使用可用工具一步步解决问题。

可用工具:
- get_weather(city): 查询实时天气
- get_attraction(city, weather): 推荐旅游景点
- book_hotel(city, budget): 预订酒店（低/中/高）
- get_news(city): 搜索旅游新闻
- get_current_datetime(): 查询当前时间

输出格式:
Thought: [思考过程]
Action: function_name(arg="value") 或 Finish[最终答案]

每次只输出一对Thought-Action。用户已提供的信息直接使用，不要反问。
"""

# ==================== 工具函数（从 travel_agent.py 复制过来） ====================
def get_weather(city): 
    try:
        r = requests.get(f"https://wttr.in/{city}?format=j1")
        d = r.json()['current_condition'][0]
        return f"{city}当前天气:{d['weatherDesc'][0]['value']}，气温{d['temp_C']}摄氏度"
    except: return f"天气查询失败"

def get_attraction(city, weather):
    t = TavilyClient(api_key=TAVILY_API_KEY)
    try:
        r = t.search(query=f"'{city}' 在'{weather}'天气下最值得去的旅游景点推荐及理由", search_depth="basic", include_answer=True)
        return r.get("answer") or "\n".join([f"- {x['title']}: {x['content']}" for x in r.get("results", [])])
    except: return "景点搜索失败"

def book_hotel(city, budget):
    try:
        from serpapi import GoogleSearch
        s = GoogleSearch({
            "engine": "google_hotels", "q": f"{city} hotel", "gl": "cn", "hl": "zh-cn",
            "currency": "CNY", "check_in_date": datetime.now().strftime("%Y-%m-%d"),
            "check_out_date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
            "adults": "2", "api_key": REAL_HOTEL_API_KEY
        })
        hotels = s.get_dict().get("properties", [])[:3]
        if hotels:
            items = []
            for h in hotels:
                r = h.get("rates_per_night", {})
                p = r.get("lowest", "暂无") if isinstance(r, dict) else "暂无"
                items.append(f"- {h.get('name', '未知')}: ¥{p}/晚")
            return f"🏨 在{city}为您找到以下真实酒店:\n" + "\n".join(items)
    except: pass
    return {"低": f"{city}经济型约200元/晚", "中": f"{city}舒适型约500元/晚", "高": f"{city}豪华型约1500元/晚"}.get(budget, f"{city}舒适型约500元/晚")

def get_news(city):
    t = TavilyClient(api_key=TAVILY_API_KEY)
    try:
        r = t.search(query=f"{city} 旅游 新闻 最近 活动", search_depth="basic")
        items = [f"- {x['title']}: {x['content']}" for x in r.get("results", [])[:3]]
        return f"关于{city}的最新旅游新闻:\n" + "\n".join(items) if items else "暂无相关新闻"
    except: return "新闻搜索失败"

def get_current_datetime():
    n = datetime.now()
    return f"现在是{n.year}年{n.month}月{n.day}日，{n.hour}时{n.minute}分"

available_tools = {
    "get_weather": get_weather, "get_attraction": get_attraction,
    "book_hotel": book_hotel, "get_news": get_news,
    "get_current_datetime": get_current_datetime
}

# ==================== Agent 逻辑 ====================
class LLM:
    def __init__(self): self.c = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
    def run(self, p, s):
        r = self.c.chat.completions.create(model="deepseek-chat", messages=[{'role':'system','content':s},{'role':'user','content':p}])
        return r.choices[0].message.content

def run_agent(msg):
    llm = LLM()
    h = [f"用户请求: {msg}"]
    for _ in range(5):
        p = "\n".join(h)
        out = llm.run(p, AGENT_SYSTEM_PROMPT)
        m = re.search(r'(Thought:.*?Action:.*?)(?=\n\s*(?:Thought:|Action:|Observation:)|\Z)', out, re.DOTALL)
        if m and m.group(1).strip() != out.strip(): out = m.group(1).strip()
        h.append(out)
        am = re.search(r"Action: (.*)", out, re.DOTALL)
        if not am: h.append("Observation: 解析失败"); continue
        a = am.group(1).strip()
        if a.startswith("Finish"):
            fm = re.match(r"Finish\[(.*)\]", a, re.DOTALL)
            return (fm.group(1) if fm else a.replace("Finish","").strip("[]: ")).strip()
        tm = re.search(r"(\w+)\(([^)]*)\)", a)
        if not tm: h.append(f"Observation: 格式错误 - {a}"); continue
        tool, args = tm.group(1), tm.group(2)
        kw = dict(re.findall(r'(\w+)="([^"]*)"', args))
        obs = available_tools[tool](**kw) if tool in available_tools else f"未定义工具 {tool}"
        h.append(f"Observation: {obs}")
    return "抱歉，暂时无法完成请求。"

# ==================== Gradio 聊天界面 ====================
def chat_fn(message, history):
    return run_agent(message)

iface = gr.ChatInterface(
    fn=chat_fn,
    title="🌈 智能旅行助手",
    description="帮你查天气、推荐景点、预订酒店、搜索新闻",
)
if __name__ == "__main__":
    iface.launch()