#main.py
from py_code.agent import llm 
from py_code.modbus_test_graph import test_graph
import asyncio
import json

# ==================== 主函数（异步） ====================
'''
async def main():
    """异步主函数，负责交互循环"""
    print("🤖 文件助手已启动，输入 “/exit()” 或 “/quit()” 退出。\n或者向我表达想退出的意向。\n")
    while True:
        # 获取用户输入（同步阻塞，但整体是异步环境，这里可以接受）
        user = input("用户: ")
        if user.lower() in ("/exit()", "/quit()"):
            break

        # 调用 Agent 的异步方法 ainvoke
        # 输入格式：{"messages": [("user", 用户输入)]}
        # Agent 内部会维护完整的对话历史，并最终返回包含所有消息的结果
        result = await agent.ainvoke({"messages": [("user", user)]})

        # 从结果中提取最后一条 AI 消息的内容并打印
        # result["messages"] 是一个列表，最后一条是 AI 的回复
        print("助手:", result["messages"][-1].content)
'''

# 定义解析函数
async def parse_test_params(user_input: str):
    """
    调用 LLM 从用户输入中提取测试参数。
    返回 (target_speed, max_cycles, error_tolerance)
    若解析失败则返回默认值 (500, 3, 5.0)
    """
    # 设计提示词，要求 LLM 只输出 JSON
    prompt = f"""
你是一个参数提取助手。请从以下用户输入中提取电机测试参数：
- 目标转速（整数）
- 循环次数（整数，默认为 3）
- 误差容限（浮点数，百分比，默认为 5.0）

如果用户没有明确指定某个参数，则使用默认值。
请输出你的观点后，返回一个 JSON 对象，格式如下：
{{"target_speed": 500, "max_cycles": 3, "error_tolerance": 5.0}}

用户输入：{user_input}
"""
    try:
        print("LLM处理")
        response = await llm.ainvoke(prompt)
        text = response.content
        print("输出的json为：\n"+text)
        
        # 尝试从响应中提取 JSON（可能前后有额外文字）
        start = text.find('{')
        end = text.rfind('}') + 1
        if start != -1 and end > start:
            params = json.loads(text[start:end])
            target = params.get("target_speed", 500)
            cycles = params.get("max_cycles", 3)
            tolerance = params.get("error_tolerance", 5.0)
            return target, cycles, tolerance
    except Exception as e:
        print(f"解析参数出错: {e}")
    # 解析失败，返回默认值
    return 500, 3, 5.0


async def main():
    '''
    Brief:
        异步主函数
    '''
    print("Modbus 测试 Agent 已启动。")
    print("你可以用自然语言告诉我测试参数，例如：")
    print("  “帮我测试电机转速 800，重复 2 次，允许 3% 误差”\n")
    while True:
        user = input("\n你: ")
        if user.lower() in ("/exit", "/quit"): #转换用户输入为小写，匹配元组数据，成功后打断循环
            break
        
        '''
        # 这里简单解析用户意图（实际可交给 LLM 解析，但先硬编码示例）
        # 为简化，假设用户输入格式: "测试转速 500 重复 3 误差 5"
        # 或者直接使用固定测试参数
        if "测试转速" in user: # 如果用户输入中有测试转速
            # 简单提取数字（实际应用可用正则或 LLM 提取）
            parts = user.split() # 将字符串按空格、换行、制表符等分割多个部分，并返回一个列表
            target = 500 # 目标
            cycles = 3 # 循环次数
            tolerance = 5.0 # 偏差
            for i, p in enumerate(parts): # 遍历：enumerate(parts) 。输入参数是 1、成员是syr的可迭代对象，第二个参数是 int 初值为0 。返回值是一个元组：(索引, 元素) i、p 的数据来自遍历函数的返回。iterable: Iterable[str] 第一个参数 的类型是 Iterable[限制可以是str与int之类的]，即元素为字符串的可迭代对象（如列表 ["a","b"]、元组、字符串等）。
                if p.isdigit(): # 如果是数字的
                    if target == 500: # 遍历后匹配字符串串
                        target = int(p)
                    elif cycles == 3:
                        cycles = int(p)
            if "误差" in user:
                for i, p in enumerate(parts):
                    if p == "误差" and i+1 < len(parts): # 先匹配到关键字后，在进行长度安全检查。完事后在提取str转换到浮点数
                        tolerance = float(parts[i+1].rstrip('%')) # rstrip匹配str后面符合的在移除，从后向前匹配重复移除匹配的，直到遇到第一个不符合的为止。
                        break
        else:
            # 默认测试参数
            target, cycles, tolerance = 500, 3, 5.0
        '''

        # 调用 LLM 解析参数
        target, cycles, tolerance = await parse_test_params(user)
        print(f"解析结果: 目标转速={target}, 循环={cycles}, 误差容限={tolerance}%")

        # 打印信息检查字符匹配
        print(f"开始测试: 目标转速={target}, 循环={cycles}, 误差容限={tolerance}%") 
        init_state = { # 定义一个组完事后直接开始赋值
            "target_speed": target,
            "max_cycles": cycles,
            "error_tolerance": tolerance,
            "current_cycle": 0,
            "retry_count": 0,
            "actual_speed": None,
            "error_msg": None,
            "last_action": "start"
        }
        # ainvoke是LangGraph的一个异步调用方法，用于启动图的执行。接收到参数后会自动运行整个图。
        final_state = await test_graph.ainvoke(init_state) # 异步调用并传入参数，并直接提取返回状态。这里会循环
        print("\n=== 测试完成 ===")
        print(f"最终状态: 完成循环数 {final_state['current_cycle']}/{cycles}")
        if final_state.get("error_msg"):
            print(f"错误: {final_state['error_msg']}")
        else:
            print("所有测试通过！")


# ==================== 程序入口 ====================
if __name__ == "__main__":
    # 运行异步主函数
    # asyncio.run() 是 Python 异步程序的启动方式
    asyncio.run(main())
