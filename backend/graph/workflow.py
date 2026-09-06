from langgraph.graph import StateGraph
from langgraph.graph import START, END

from graph.state import VentureState

from agents.supervisor import supervisor_agent
from agents.market import market_agent
from agents.competitor import competitor_agent
from agents.business import business_agent
from agents.risk import risk_agent
from agents.report import report_agent
from rag.retriever import retrieve_context_node

builder = StateGraph(VentureState)

builder.add_node("supervisor", supervisor_agent)
builder.add_node("retrieve_context", retrieve_context_node)
builder.add_node("market", market_agent)
builder.add_node("competitor", competitor_agent)
builder.add_node("business", business_agent)
builder.add_node("risk", risk_agent)
builder.add_node("report", report_agent)

builder.add_edge(START, "supervisor")
builder.add_edge("supervisor", "retrieve_context")

# Ordered chain of optional agents. After each one (or if it's skipped),
# routing falls through to the next task the supervisor actually selected,
# and once the chain is exhausted everything converges on "report".
AGENT_ORDER = ["market", "competitor", "business", "risk"]


def make_router(current: str):
    """
    Returns a routing function that, given the current position in
    AGENT_ORDER, sends execution to the next selected task, skipping any
    agent the supervisor didn't choose.
    """
    remaining = AGENT_ORDER[AGENT_ORDER.index(current) + 1:]

    def router(state):
        tasks = state.get("tasks", [])
        for candidate in remaining:
            if candidate in tasks:
                return candidate
        return "report"

    return router


def entry_router(state):
    tasks = state.get("tasks", [])
    for candidate in AGENT_ORDER:
        if candidate in tasks:
            return candidate
    return "report"


builder.add_conditional_edges(
    "retrieve_context",
    entry_router,
    {**{a: a for a in AGENT_ORDER}, "report": "report"},
)

for agent_name in AGENT_ORDER:
    router = make_router(agent_name)
    targets = {a: a for a in AGENT_ORDER[AGENT_ORDER.index(agent_name) + 1:]}
    targets["report"] = "report"
    builder.add_conditional_edges(agent_name, router, targets)

builder.add_edge("report", END)

graph = builder.compile()
