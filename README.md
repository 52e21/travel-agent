# 🌈 智能旅行助手

一个基于 DeepSeek 大模型的 AI 旅行助手，可以帮你查天气、推荐景点、预订酒店、搜索最新旅游新闻。

## 功能
- 🌤️ 实时天气查询（wttr.in）
- 🏛️ 智能景点推荐（Tavily 搜索）
- 🏨 酒店预订
- 📰 最新旅游新闻
- 💬 彩色聊天界面（PyWebIO）

## 技术栈
- Python
- DeepSeek API（大模型推理）
- Tavily API（实时搜索）
- PyWebIO（Web 界面）

## 如何使用

1. 克隆仓库
2. 安装依赖：`pip install -r requirements.txt`
3. 在项目文件夹创建 `config.py`，填入你的 API 密钥：
   ```python
   DEEPSEEK_API_KEY = "你的密钥"
   TAVILY_API_KEY = "你的密钥"
   REAL_HOTEL_API_KEY = "你的SerpApi密钥"

## 测试评估

对 15 个典型旅行场景进行自动化测试，覆盖单工具调用、多工具编排、简短输入等场景。

| 编号 | 测试场景 | 预期工具 | 结果 | 耗时 |
|------|---------|---------|------|------|
| 1 | 单工具：天气查询 | get_weather | ✅ | 5.5s |
| 2 | 单工具：景点推荐 | get_attraction | ✅ | 6.9s |
| 3 | 单工具：酒店预订 | book_hotel | ✅ | 5.9s |
| 4 | 单工具：新闻搜索 | get_news | ✅ | 5.1s |
| 5 | 单工具：时间查询 | get_current_datetime | ✅ | 2.0s |
| 6 | 多工具：天气→景点 | 2 工具 | ✅ | 7.2s |
| 7 | 多工具：天气→景点→酒店 | 3 工具 | ✅ | 20.9s |
| 8 | 多工具：新闻→天气 | 2 工具 | ✅ | 8.6s |
| 9 | 简短输入：天气+酒店 | 2 工具 | ✅ | 18.6s |
| 10 | 简短输入：天气+酒店(高预算) | 2 工具 | ❌ | 25.5s |
| 11 | 多工具：新闻→景点 | 2 工具 | ✅ | 22.8s |
| 12 | 单工具：景点推荐 | get_attraction | ✅ | 11.2s |
| 13 | 简短输入：高预算酒店 | book_hotel | ✅ | 18.1s |
| 14 | 多工具：天气→新闻 | 2 工具 | ✅ | 7.3s |
| 15 | 多工具：酒店→景点 | 2 工具 | ✅ | 18.9s |

### 汇总
- **总用例**: 15
- **成功率**: 93.3%
- **平均耗时**: 12.3 秒
- **覆盖工具**: 全部 5 个工具（天气、景点、酒店、新闻、时间）
- **多工具编排**: 7 个用例覆盖 2-3 工具联动

## 系统架构
```mermaid
graph TB
    User[👤 用户] --> Frontend[🌐 Web 前端]
    Frontend --> Agent[🤖 Agent 核心循环]
    
    Agent --> LLM[🧠 DeepSeek 大模型]
    Agent --> Tools[🔧 工具层]
    
    Tools --> Weather[🌤️ wttr.in 天气]
    Tools --> Search[🔍 Tavily 搜索]
    Tools --> Hotel[🏨 SerpApi 酒店]
    Tools --> Time[⏰ 系统时间]
    
    LLM --> |Thought| Agent
    Agent --> |Action| Tools
    Tools --> |Observation| Agent