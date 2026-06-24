# 🌈 智能旅行助手

一个基于 DeepSeek 大模型的 AI 旅行助手，实现 Thought-Action-Observation 智能体循环，支持多工具协同调用。作为 Agent 开发方向的实践项目，完整覆盖了 Agent 设计、工具集成、 评估测试和 API 服务化。

## 功能
- 🌤️ 实时天气查询（wttr.in）
- 🏛️ 智能景点推荐（Tavily 搜索）
- 🏨 酒店预订
- 📰 最新旅游新闻
- 💬 彩色聊天界面（PyWebIO）

## 技术栈
- **大模型**: DeepSeek API
- **Agent 架构**: Thought-Action-Observation 循环 / 工具调用 / System Prompt 设计
- **后端**: Python / FastAPI
- **搜索**: Tavily API / SerpApi
- **前端**: PyWebIO
- **测试**: 自动化测试脚本 / 15 条评估用例

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

## 已知限制

| 限制 | 说明 | 解决方案 |
|------|------|----------|
| 酒店 API 依赖 | SerpApi 需要付费 API Key，未配置时自动降级为模拟数据 | 代码已预留接口，替换真实 API 只需修改函数体 |
| 复杂多工具任务 | 极简短输入 + 多工具调用可能超过循环次数限制（5 轮） | 增加循环上限或引导用户输入更详细的需求 |
| 未做持久化记忆 | 当前仅支持会话内上下文，关闭浏览器后历史丢失 | 后续可接入 Chroma 向量数据库做长期记忆 |

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

## Agent 工作流程

1. 用户输入需求（如"北京天气怎么样？推荐一个景点"）
2. Agent 进入 **Thought** 阶段：分析用户意图，决定调用哪个工具
3. Agent 执行 **Action**：调用对应 API（天气、搜索、酒店等）
4. 工具返回 **Observation**：Agent 获取结果，判断是否需要继续
5. 循环直到 Agent 认为信息足够，输出最终回复