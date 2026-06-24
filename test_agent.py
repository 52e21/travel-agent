"""
智能旅行助手 - 自动化测试脚本
运行方式：python test_agent.py
"""
import os
import sys
import time

# 从主程序导入 run_agent
from travel_agent import run_agent, available_tools

# ==================== 测试用例 ====================
test_cases = [
    # (用户输入, 预期调用的工具列表, 测试说明)
    ("北京今天天气如何？", ["get_weather"], "单工具：天气查询"),
    ("南京有什么好玩的景点？", ["get_attraction"], "单工具：景点推荐（无天气前缀）"),
    ("帮我订一家上海的低预算酒店", ["book_hotel"], "单工具：酒店预订"),
    ("最近杭州有什么旅游新闻？", ["get_news"], "单工具：新闻搜索"),
    ("今天是几号？", ["get_current_datetime"], "单工具：时间查询"),
    ("深圳天气怎样？推荐一个适合拍照的景点", ["get_weather", "get_attraction"], "多工具：天气→景点"),
    ("成都下雨的话去哪里玩？帮我订中档酒店", ["get_weather", "get_attraction", "book_hotel"], "多工具：天气→景点→酒店"),
    ("广州有什么最新活动？天气怎么样？", ["get_news", "get_weather"], "多工具：新闻→天气"),
    ("重庆，今天出发，预算500", ["get_weather", "book_hotel"], "简短输入：天气+酒店"),
    ("北京，天气，今日出发，预算20000", ["get_weather", "book_hotel"], "简短输入：天气+酒店（高预算）"),
    ("苏州最近有什么音乐节？推荐一个人少的景点", ["get_news", "get_attraction"], "多工具：新闻→景点"),
    ("武汉适合带孩子去的景点有哪些？", ["get_attraction"], "单工具：景点推荐"),
    ("西安，豪华酒店", ["book_hotel"], "简短输入：高预算酒店"),
    ("长沙的天气怎么样？最近有什么新闻？", ["get_weather", "get_news"], "多工具：天气→新闻"),
    ("厦门，经济型酒店，推荐看海的景点", ["book_hotel", "get_attraction"], "多工具：酒店→景点"),
]

# ==================== 运行测试 ====================
def run_tests():
    print("=" * 60)
    print("智能旅行助手 - 自动化测试")
    print("=" * 60)
    
    results = []
    total = len(test_cases)
    passed = 0
    
    for i, (user_input, expected_tools, description) in enumerate(test_cases, 1):
        print(f"\n[{i}/{total}] {description}")
        print(f"输入: {user_input}")
        print(f"预期工具: {expected_tools}")
        
        start_time = time.time()
        try:
            # 调用 Agent（每次独立，不传历史）
            reply = run_agent(user_input)
            elapsed = round(time.time() - start_time, 2)
            
            # 简单判断：只要返回了非错误信息就算成功
            success = "抱歉" not in reply and "错误" not in reply
            
            if success:
                passed += 1
                status = "✅"
            else:
                status = "❌"
            
            print(f"耗时: {elapsed}秒 | 结果: {status}")
            print(f"回复: {reply[:100]}...")  # 只显示前100字
            
        except Exception as e:
            elapsed = round(time.time() - start_time, 2)
            status = "❌"
            reply = f"异常: {e}"
            print(f"耗时: {elapsed}秒 | 结果: {status}")
            print(f"错误: {e}")
        
        results.append({
            "编号": i,
            "描述": description,
            "输入": user_input,
            "预期工具": ", ".join(expected_tools),
            "成功": status == "✅",
            "耗时(秒)": elapsed,
        })
        
        # 避免 API 限流
        time.sleep(1)
    
    # ==================== 打印汇总 ====================
    print("\n" + "=" * 60)
    print("测试汇总")
    print("=" * 60)
    print(f"总用例: {total}")
    print(f"成功: {passed}")
    print(f"失败: {total - passed}")
    print(f"成功率: {round(passed/total*100, 1)}%")
    
    print("\n详细结果:")
    print("-" * 80)
    print(f"{'编号':<5}{'描述':<25}{'成功':<8}{'耗时':<10}")
    print("-" * 80)
    for r in results:
        status = "✅" if r["成功"] else "❌"
        print(f"{r['编号']:<5}{r['描述']:<25}{status:<8}{r['耗时(秒)']:<10}")
    
    return results

if __name__ == "__main__":
    results = run_tests()