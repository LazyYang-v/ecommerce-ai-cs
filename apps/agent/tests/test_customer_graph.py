import asyncio

from app.graphs.customer_graph import customer_graph


def test_graph_returns_deterministic_response():
    result = customer_graph.invoke({"message": "测试", "response": ""})
    assert result["response"] == "已收到消息：测试"


def test_graph_async_invoke():
    result = asyncio.run(customer_graph.ainvoke({"message": "异步", "response": ""}))
    assert result["response"] == "已收到消息：异步"
