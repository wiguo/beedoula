from __future__ import annotations

import os
from typing import List

from langchain_tavily import TavilySearch

from app.memory import get_baby_profile, save_baby_fact
from app.rag import retrieve_information


def get_tool_belt() -> List:
    tools = [retrieve_information, get_baby_profile, save_baby_fact]
    if os.environ.get("TAVILY_API_KEY"):
        tools.insert(0, TavilySearch(max_results=5))
    return tools
