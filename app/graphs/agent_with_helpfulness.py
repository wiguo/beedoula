"""An agent graph with a post-response helpfulness check loop.

After the agent responds, a judge model evaluates whether the response is
helpful for the initial query. If helpful, the run ends; otherwise the graph
loops back to the agent for another attempt, with a message-count guard to
prevent infinite loops.
"""

from __future__ import annotations

from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from app.graphs.simple_agent import SYSTEM_PROMPT
from app.models import get_chat_model
from app.state import MessagesState
from app.tools import get_tool_belt

LOOP_MESSAGE_LIMIT = 10


def call_model(state: MessagesState) -> dict:
    """Invoke the tool-bound model with the accumulated messages."""
    model = get_chat_model().bind_tools(get_tool_belt())
    messages = state["messages"]
    if not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=SYSTEM_PROMPT), *messages]
    return {"messages": [model.invoke(messages)]}


def route_to_action_or_helpfulness(state: MessagesState):
    """Execute requested tools, otherwise evaluate the response's helpfulness."""
    if getattr(state["messages"][-1], "tool_calls", None):
        return "action"
    return "helpfulness"


_helpfulness_prompt = ChatPromptTemplate.from_template(
    "Given an initial query and a final response, determine if the final response "
    "is extremely helpful or not. Respond with only Y or N.\n\n"
    "Initial Query:\n{initial_query}\n\n"
    "Final Response:\n{final_response}"
)


def helpfulness_node(state: MessagesState) -> dict:
    """Judge the latest response against the initial query."""
    if len(state["messages"]) > LOOP_MESSAGE_LIMIT:
        return {"messages": [AIMessage(content="HELPFULNESS:END")]}

    initial_query = state["messages"][0]
    final_response = state["messages"][-1]

    chain = _helpfulness_prompt | get_chat_model() | StrOutputParser()
    result = chain.invoke(
        {
            "initial_query": initial_query.content,
            "final_response": final_response.content,
        }
    )

    decision = "Y" if result.strip().upper().startswith("Y") else "N"
    return {"messages": [AIMessage(content=f"HELPFULNESS:{decision}")]}


def helpfulness_decision(state: MessagesState):
    """End on a helpful response (or loop-limit hit); otherwise retry."""
    text = getattr(state["messages"][-1], "content", "")
    if "HELPFULNESS:END" in text or "HELPFULNESS:Y" in text:
        return "end"
    return "continue"


def build_graph():
    """Build the agent graph with the helpfulness evaluation loop."""
    graph = StateGraph(MessagesState)
    graph.add_node("agent", call_model)
    graph.add_node("action", ToolNode(get_tool_belt()))
    graph.add_node("helpfulness", helpfulness_node)
    graph.add_edge(START, "agent")
    graph.add_conditional_edges(
        "agent",
        route_to_action_or_helpfulness,
        {"action": "action", "helpfulness": "helpfulness"},
    )
    graph.add_conditional_edges(
        "helpfulness",
        helpfulness_decision,
        {"continue": "agent", "end": END},
    )
    graph.add_edge("action", "agent")
    return graph


graph = build_graph().compile()
