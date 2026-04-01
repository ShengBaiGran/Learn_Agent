#main.py
from agent import agent
import asyncio

# ==================== 主函数（异步） ====================
async def main():
    """异步主函数，负责交互循环"""
    print("🤖 文件助手已启动，输入 “/exit()” 或 “/quit()” 退出。\n      或者向我表达想退出的意向。\n")
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

# ==================== 程序入口 ====================
if __name__ == "__main__":
    # 运行异步主函数
    # asyncio.run() 是 Python 异步程序的启动方式
    asyncio.run(main())
