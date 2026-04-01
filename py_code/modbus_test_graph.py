#modbus_test_graph.py
from typing import TypedDict, Optional, List, Annotated
from langgraph.graph import StateGraph, END, START
import asyncio
from agent import write_holding_register, read_holding_register

DEBUG_MODE_MODBUS_TEST: bool = True

#创建一个类，定义所有的状态
'''
notes:
    这里的last_action应该有规范的标准(暂时只有这几个)
    read
    write
    f"wait {}s"
    validate_error
    validate_success
    validate_fail
'''
class TestState(TypedDict):
    #用户目标
    target_speed: int #目标速度
    max_cycles: int   #总循环次数
    error_tolerance: float #误差容忍百分比（5.0表示+-5%）

    #运行中间态
    current_cycle: int                  # 当前以完成循环次数
    retry_count: int                    # 当前循环内重试次数
    actual_speed: Optional[int]         # 当前读取到的实际转速 这个Optional[int]等价于 union[int, None]
    error_msg: Optional[str]            # 错误信息
    last_action: str                    # 最后执行的动作（用于调试）


#定义节点(每个节点为异步的函数)
async def write_speed(state: TestState) -> TestState:#异步定义一个函数
    """
    brief：写速度
    Args:
        state: 实际的结构体
    Returns:
        TestState: 返回修改后的结构体
    Notes:
        节点1：写入目标转速
    """
#函数体
    if DEBUG_MODE_MODBUS_TEST:
        print("调用write_speed()")#调试用

    success: bool = await write_holding_register(0x02, state["target_speed"], 1)#这里由于使用了异步函数，调用时要用await
    if not success: #返回的值是bool 如果是false那就输出错误报告
        state["error_msg"] = "目标速度写入失败"
    else:
        state["error_msg"] = None
    state["last_action"] = "write"
    return state

async def wait_stable(state: TestState) -> TestState:
    """
    brief：等待
    Args:
        state: 实际的结构体
    Returns:
        TestState: 返回修改后的结构体
    Notes:
        节点2：等待数据稳定
    """
#函数体
    if DEBUG_MODE_MODBUS_TEST:
        print("调用wait_stable()")#调试用

    time_s: float = 1.0
    await asyncio.sleep(time_s)
    state["last_action"] = f"wait {time_s}s"
    return state

async def read_speed(state: TestState) -> TestState:
    """
    brief：读速度
    Args:
        state: 实际的结构体
    Returns:
        TestState: 返回修改后的结构体
    Notes:
        节点3：读取实际转速
    """
#函数体
    if DEBUG_MODE_MODBUS_TEST:
        print("调用read_speed()")#调试用

    value: Optional[int] = await read_holding_register(0x12, 1)
    state["actual_speed"] = value
    if value == None:
        state["error_msg"] = "数据读取失败"
    else:
        state["error_msg"] = None

    state["last_action"] = "read"
    return state

async def validate(state: TestState) -> TestState:
    """
    brief:
        用于验证实际与目标
    Args:
        state: 实际的结构体
    Returns:
        TestState: 返回修改后的结构体
    Notes:
        节点4：校验误差并决定下一步，不跳转之更新方向
        具体逻辑为：
        先从传入的结构体中拿数据，实际速度无错误后，计算偏差比---与。
        如果偏差比较大增加重试计数并保留错误信息。
        如果成功清楚所有额错误，增加循环计数
    """
#函数体
    if DEBUG_MODE_MODBUS_TEST:
        print("调用validate()")#调试用

    target_speed: int = state["target_speed"]#预期这个是存在的所有不用get
    actual_speed: int = state.get("actual_speed")#关于这里的get，AI说是为了安全性。防止你要的参数是无效的。这里如果无效的话就返回None。
    if actual_speed is None:
        state["error_msg"] = "无实际转速数据"
        state["last_action"] = "validate_error"
        return state
    
    error_percent: float = 0.0
    if target_speed == 0:
        error_percent = 0.0 if actual_speed == 0 else 100.0
    else:
        error_percent = (abs(float(actual_speed) - float(target_speed)) / float(target_speed)) * 100.0
    
    if error_percent <= state["error_tolerance"]:
        state["error_msg"] = None
        state["current_cycle"] = state.get("current_cycle", 0) + 1
        state["retry_count"] = 0
        state["last_action"] = "validate_success"
    else:
        state["error_msg"] = f"误差 {error_percent:.1f}% 超过 {state['error_tolerance']}%"
        state["retry_count"] = state.get("retry_count", 0) + 1
        state["last_action"] = "validate_fail"
    return state

#定义路由函数（条件边）
#根据state的值，决定下一个节点

# 在 write_speed 之后，总是进入 wait_stable
# 在 wait_stable 之后，总是进入 read_speed
# 在 read_speed 之后，总是进入 validate

# 这里不用异步函数，改用同步函数
'''
Q:为什么有时候用异步有时候用同步？
A:在 Python 异步编程中，任何使用了 await 的函数，其本身必须定义为 async def，
而调用它的函数也必须在 async def 中使用 await 调用，形成一个“异步传染链”。
'''
def after_validate(state: TestState) -> str:
    '''
    Brief: 
        在 validate 之后，需要条件路由
    Args: 
        state: TestState实际的结构体
    Returns: 
        str: 返回修改后的结构体
    Notes:
        4级门控
    '''
#函数实体
    if DEBUG_MODE_MODBUS_TEST:
        print("调用after_validate()")#调试用

    if state["current_cycle"] >= state["max_cycles"]:
        return "end"
    
    if state.get("error_msg") and state.get("retry_count", 0) < 3:
        return "retry"
    
    if state.get("error_msg"):
        return "end_with_error"
    
    return "next_cycle"

#构建StateGraph（状态图）
builder = StateGraph(TestState)

#添加节点
builder.add_node("write", write_speed)
builder.add_node("wait", wait_stable)
builder.add_node("read", read_speed)
builder.add_node("validate", validate)

#设置入口点
builder.set_entry_point("write")

#添加固定边
builder.add_edge("write", "wait")
builder.add_edge("wait", "read")
builder.add_edge("read", "validate")

#添加条件边
builder.add_conditional_edges(
    "validate",
    after_validate,
    {
        "end": END,
        "retry": "write",
        "next_cycle": "write",
        "end_with_error": END,
    }
)

#编译图
test_graph = builder.compile()

