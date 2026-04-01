#main.py
#from agent import agent # 暂时不使用
from modbus_test_graph import test_graph
import asyncio

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

async def main():
    '''
    Brief:
        异步主函数
    '''
    print("Modbus 测试 Agent 已启动。")
    print("示例命令: 测试转速 500 重复 3 误差 5 \n注意必须要这样。因为这只是关键字识别，没有接入LLM，只用于验证LangGraph的流程图。")
    while True:
        user = input("\n你: ")
        if user.lower() in ("/exit", "/quit"):
            break
        
        # 这里简单解析用户意图（实际可交给 LLM 解析，但先硬编码示例）
        # 为简化，假设用户输入格式: "测试转速 500 重复 3 误差 5"
        # 或者直接使用固定测试参数
        if "测试转速" in user:
            # 简单提取数字（实际应用可用正则或 LLM 提取）
            parts = user.split()
            target = 500
            cycles = 3
            tolerance = 5.0
            for i, p in enumerate(parts):
                if p.isdigit():
                    if target == 500:
                        target = int(p)
                    elif cycles == 3:
                        cycles = int(p)
            if "误差" in user:
                for i, p in enumerate(parts):
                    if p == "误差" and i+1 < len(parts):
                        tolerance = float(parts[i+1].rstrip('%'))
                        break
        else:
            # 默认测试参数
            target, cycles, tolerance = 500, 3, 5.0
        
        print(f"开始测试: 目标转速={target}, 循环={cycles}, 误差容限={tolerance}%")
        init_state = {
            "target_speed": target,
            "max_cycles": cycles,
            "error_tolerance": tolerance,
            "current_cycle": 0,
            "retry_count": 0,
            "actual_speed": None,
            "error_msg": None,
            "last_action": "start"
        }
        final_state = await test_graph.ainvoke(init_state)#会在这里循环知道结束
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
