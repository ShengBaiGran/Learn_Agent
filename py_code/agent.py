#agent.py
# 导入标准库
import os          # 提供与操作系统交互的功能（文件、路径等）
import asyncio     # 异步 I/O 库，用于支持 async/await 语法

# 导入第三方库
from dotenv import load_dotenv          # 从 .env 文件加载环境变量
from pathlib import Path                # 面向对象的文件路径处理
from langchain_deepseek import ChatDeepSeek   # DeepSeek 模型的 LangChain 封装
from langchain_core.tools import tool        # 用于将普通函数装饰为 AI 可调用的工具
from langchain.agents import create_agent   # 更加新的预设Agent ReAct循环
from langchain.agents.middleware import (
    SummarizationMiddleware,  # 自动总结长对话
    HumanInTheLoopMiddleware  # 敏感操作需人工确认
)

from typing import Optional

# ===== 模拟 Modbus 设备的状态（真实项目中替换为 pymodbus 调用）=====
_device_register = 0x00 #模拟寄存器的值

async def write_holding_register(addr: int, value: int, unit: int = 1) -> bool:
    """模拟写保持寄存器"""
    global _device_register
    # 模拟写入延迟（真实会有延迟这里软件替代）
    await asyncio.sleep(0.1) #秒
    _device_register = value
    print(f"[DEBUG] 写入寄存器 {addr} 值 {value}")
    return True

async def read_holding_register(addr: int, unit: int = 1) -> Optional[int]:
    """模拟读寄存器"""
    global _device_register
    await asyncio.sleep(0.1)
    print(f"[DEBUG] 读取寄存器 {addr} 值 {_device_register}")
    return _device_register

# ==================== 环境变量加载 ====================
# 当前脚本的绝对路径：例如 D:\...\py_code\file_agent.py
# .parent 得到 py_code 目录，再 .parent 得到 base_agent 根目录
# 最终定位到根目录下的 .env 文件
env_path = Path(__file__).parent.parent / '.env'
# 显式指定 .env 文件路径，避免因工作目录不同而找不到文件
load_dotenv(dotenv_path=env_path)

# 可选：打印 API Key 的前缀，用于调试（已注释）
# print(repr(os.getenv("DEEPSEEK_API_KEY")))

# ==================== 定义工具（Tool） ====================
# @tool 装饰器将普通 Python 函数转换为 AI Agent 可以调用的“工具”
# Agent 会根据用户输入自动判断是否需要调用这些工具，并自动提取参数

@tool
def write_file(filename: str, content: str) -> str:
    """
    写入文件（自动创建目录）
    参数：
        filename: 文件路径（相对或绝对）
        content:  要写入的文本内容
    返回：
        操作结果字符串（成功或错误信息）
    """
    try:
        # os.path.dirname 获取文件所在目录，如果目录不存在则递归创建
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        # 以写入模式打开文件，编码 utf-8 保证中文不乱码
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"✅ 已写入 {filename}"
    except Exception as e:
        return f"❌ 失败: {e}"

@tool
def read_file(filename: str) -> str:
    """
    读取文件内容
    参数：
        filename: 文件路径
    返回：
        文件内容或错误信息
    """
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        return f"📄 {filename} 内容：\n{content}"
    except FileNotFoundError:
        return f"❌ 文件 {filename} 不存在"
    except Exception as e:
        return f"❌ 读取失败: {e}"

@tool
def create_file(filename: str) -> str:
    """
    创建空文件（若文件已存在则提示）
    参数：
        filename: 文件路径
    返回：
        操作结果字符串
    """
    if os.path.exists(filename):
        return f"⚠️ 文件 {filename} 已存在"
    try:
        # 'w' 模式写入空内容即创建空文件
        with open(filename, 'w') as f:
            pass   # 不写入任何内容
        return f"✅ 已创建空文件 {filename}"
    except Exception as e:
        return f"❌ 创建失败: {e}"

@tool
def list_directory(path: str = ".") -> str:
    """
    列出目录内容
    参数：
        path: 目录路径，默认为当前目录（"."）
    返回：
        目录下所有文件和子目录的列表
    """
    try:
        items = os.listdir(path)
        # 生成多行文本，每行前加两个空格和短横线
        return "📁 目录内容：\n" + "\n".join(f"  - {i}" for i in items)
    except Exception as e:
        return f"❌ 错误: {e}"
    

@tool
def exit_agent(cmd: str):
    '''
    直接退出python环境
    '''
    exit()

# ==================== 初始化 AI 模型 ====================
# 创建 DeepSeek 对话模型实例
# model="deepseek-chat" : 使用 DeepSeek 的通用对话模型
# temperature=0.1       : 低温度使输出更稳定、更保守，适合确定性任务
# 注意：API Key 通过环境变量 DEEPSEEK_API_KEY 自动读取（由 load_dotenv 加载）
llm = ChatDeepSeek(model="deepseek-chat", temperature=0.1)

# 将上面定义的四个工具放入列表，供 Agent 使用
tools = [write_file, read_file, create_file, list_directory, exit_agent]

# ==================== 创建 ReAct Agent ====================
# create_react_agent 是 LangGraph 预置的智能体构建函数
# 它实现了一个标准的“思考-行动-观察”循环（Reasoning + Acting）
# 内部自动处理：用户输入 → LLM 决策 → 调用工具 → 观察结果 → 再次决策 → 最终回答
agent = create_agent(model=llm, 
                     tools=tools,
                     system_prompt="你是一个专业的文件管理助手。",              #加入system提示词
                     middleware=[                                             #新特性
                        SummarizationMiddleware(model=llm, max_tokens_before_summary=2000),
                        HumanInTheLoopMiddleware(interrupt_on={"delete_file": {"allowed_decisions": ["approve", "reject"]}})
                    ]
)
