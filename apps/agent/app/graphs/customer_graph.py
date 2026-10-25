from typing import TypedDict

from langgraph.graph import END, START, StateGraph


class CustomerState(TypedDict):
    message: str
    response: str


def handle_message(state: CustomerState) -> dict:
    """Phase 1 确定性测试节点。

    仅用于验证 LangGraph 图执行与服务间通信，不代表 LLM 推理；
    Phase 2 接入 DeepSeek 后由真实模型节点替换。
    """
    return {"response": f"已收到消息：{state['message']}"}


builder = StateGraph(CustomerState)
builder.add_node("handle_message", handle_message)
builder.add_edge(START, "handle_message")
builder.add_edge("handle_message", END)

customer_graph = builder.compile()
