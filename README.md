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