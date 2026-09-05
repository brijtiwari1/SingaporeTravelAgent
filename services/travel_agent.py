import os
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mcp_adapters.client import MultiServerMCPClient

from rag.retriever import retrieve, format_retrieval


# ---------------------------------------------------------
# Environment
# ---------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]

load_dotenv(ROOT / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is missing. "
        "Create a .env file in the project root and add GEMINI_API_KEY."
    )


# ---------------------------------------------------------
# RAG Tool
# ---------------------------------------------------------

@tool
def search_travel_knowledge(query: str) -> str:
    """
    Search the Singapore travel knowledge base.

    Use this tool for stable destination information such as:
    attractions, neighbourhoods, transportation, culture,
    food, local experiences, indoor/outdoor activities,
    itinerary ideas, and practical travel information.

    Do NOT use this tool for current weather or currency conversion.
    """
    try:
        docs = retrieve(query, k=6)
        return format_retrieval(docs)
    except Exception as exc:
        return f"Knowledge-base search failed: {exc}"


# ---------------------------------------------------------
# MCP Configuration
# ---------------------------------------------------------

WEATHER_SERVER = str(ROOT / "mcp_servers" / "weather_server.py")
CURRENCY_SERVER = str(ROOT / "mcp_servers" / "currency_server.py")


def create_mcp_client() -> MultiServerMCPClient:
    """
    Create MCP client for the local weather and currency servers.
    """

    return MultiServerMCPClient(
        {
            "weather": {
                "transport": "stdio",
                "command": sys.executable,
                "args": [WEATHER_SERVER],
            },
            "currency": {
                "transport": "stdio",
                "command": sys.executable,
                "args": [CURRENCY_SERVER],
            },
        }
    )


# ---------------------------------------------------------
# Gemini Model
# ---------------------------------------------------------

def create_gemini_model() -> ChatGoogleGenerativeAI:
    """
    Create the Gemini chat model used by the LangChain agent.
    """

    return ChatGoogleGenerativeAI(
    model=GEMINI_MODEL,
    google_api_key=GEMINI_API_KEY,
    max_retries=3,
    timeout=120,
)


# ---------------------------------------------------------
# System Prompt
# ---------------------------------------------------------

SYSTEM_PROMPT = """
You are a Singapore Travel Planning Assistant.

Your job is to help users plan trips to Singapore using:

1. A Singapore travel knowledge-base through the
   search_travel_knowledge tool.

2. A weather MCP tool for current/future weather information.

3. A currency MCP tool for currency conversion.

IMPORTANT TOOL RULES
--------------------

Use search_travel_knowledge when the user asks about:

- Singapore attractions
- neighbourhoods
- transportation
- culture
- food
- local experiences
- itinerary ideas
- indoor/outdoor activities
- practical travel information

Use the weather MCP tool when the user asks about:

- current weather
- tomorrow's weather
- forecast
- weather for a particular date
- adjusting an itinerary according to weather

Use the currency MCP tool when the user asks for:

- currency conversion
- INR to SGD
- SGD to INR
- prices converted between currencies

For a trip-planning request that depends on weather:

1. Retrieve relevant Singapore travel knowledge.
2. Get the weather forecast using the weather MCP tool.
3. Adjust outdoor/indoor activities according to the forecast.
4. Produce a practical itinerary.

Do not invent live weather or currency information.

If a live MCP tool fails:
- Clearly tell the user that live information could not be retrieved.
- Continue with stable knowledge where possible.
- Do not fabricate current weather or exchange rates.

RAG SOURCE RULE
---------------
When using information from the knowledge base, rely on the retrieved
content rather than inventing unsupported facts.

If source information is available, mention the relevant source title
in the final answer.

CONVERSATION RULE
-----------------
Use previous conversation context when answering follow-up questions.

For example:

User:
"Plan a 3-day Singapore trip."

User:
"Make day 2 more suitable for children."

Understand that "day 2" refers to the previously generated Singapore itinerary.

RESPONSE STYLE
--------------
Give practical, concise travel advice.

For itineraries, use:

Day 1
- Morning
- Afternoon
- Evening

Day 2
- Morning
- Afternoon
- Evening

Day 3
- Morning
- Afternoon
- Evening

Include short explanations for important choices.

Do not claim that a live tool was used unless it was actually called.
"""


# ---------------------------------------------------------
# Helper: Extract text from LangChain messages
# ---------------------------------------------------------

def message_to_text(message: Any) -> str:
    """
    Convert a LangChain message content value into normal text.
    """

    content = getattr(message, "content", "")

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts = []

        for item in content:
            if isinstance(item, str):
                parts.append(item)

            elif isinstance(item, dict):
                text = item.get("text")
                if text:
                    parts.append(str(text))

        return "\n".join(parts)

    return str(content)


# ---------------------------------------------------------
# Helper: Extract MCP tool calls
# ---------------------------------------------------------

def extract_tool_events(messages: list[Any]) -> list[dict[str, str]]:
    """
    Extract tool calls from the agent message history.
    """

    events: list[dict[str, str]] = []

    for message in messages:

        tool_calls = getattr(message, "tool_calls", None)

        if tool_calls:
            for call in tool_calls:
                name = call.get("name", "")

                if name:
                    events.append(
                        {
                            "tool": name,
                            "type": "tool_call",
                        }
                    )

        message_type = getattr(message, "type", "")

        if message_type == "tool":
            tool_name = getattr(message, "name", "")

            if tool_name:
                events.append(
                    {
                        "tool": tool_name,
                        "type": "tool_result",
                    }
                )

    # Remove duplicates while preserving order
    unique_events = []
    seen = set()

    for event in events:
        key = (event["tool"], event["type"])

        if key not in seen:
            seen.add(key)
            unique_events.append(event)

    return unique_events


# ---------------------------------------------------------
# Main Agent Function
# ---------------------------------------------------------

async def ask(
    question: str,
    history: list[Any] | None = None,
) -> dict[str, Any]:

    history = history or []

    # -----------------------------------------------------
    # Retrieve KB sources for UI/source display
    # -----------------------------------------------------

    kb_sources = []

    try:
        retrieved_docs = retrieve(question, k=6)

        seen_sources = set()

        for doc in retrieved_docs:
            title = doc.metadata.get("source_title", "Unknown source")
            url = doc.metadata.get("source_url", "")

            key = (title, url)

            if key not in seen_sources:
                seen_sources.add(key)

                kb_sources.append(
                    {
                        "title": title,
                        "url": url,
                    }
                )

    except Exception:
        # Do not stop the application if source display retrieval fails.
        kb_sources = []

    # -----------------------------------------------------
    # MCP
    # -----------------------------------------------------

    mcp_client = create_mcp_client()

    try:
        mcp_tools = await mcp_client.get_tools()

        # -------------------------------------------------
        # Gemini
        # -------------------------------------------------

        model = create_gemini_model()

        # -------------------------------------------------
        # Create LangChain agent
        # -------------------------------------------------

        agent = create_agent(
            model=model,
            tools=[
                search_travel_knowledge,
                *mcp_tools,
            ],
            system_prompt=SYSTEM_PROMPT,
        )

        # -------------------------------------------------
        # Build conversation
        # -------------------------------------------------

        messages = []

        # Keep the most recent conversation turns.
        # This prevents the prompt from growing indefinitely.
        if history:
            messages.extend(history[-12:])

        messages.append(
            {
                "role": "user",
                "content": question,
            }
        )

        # -------------------------------------------------
        # Run agent
        # -------------------------------------------------

        result = await agent.ainvoke(
            {
                "messages": messages,
            }
        )

        result_messages = result.get("messages", [])

        if not result_messages:
            raise RuntimeError("Gemini agent returned no messages.")

        final_message = result_messages[-1]

        answer = message_to_text(final_message)

        # -------------------------------------------------
        # Tool events
        # -------------------------------------------------

        tool_events = extract_tool_events(result_messages)

        # -------------------------------------------------
        # Return result to Streamlit
        # -------------------------------------------------

        return {
            "answer": answer,
            "kb_sources": kb_sources,
            "tool_events": tool_events,
            "messages": result_messages,
        }

    finally:
        # MultiServerMCPClient is intentionally kept scoped to this request.
        # This is compatible with the stateless client pattern.
        pass


# ---------------------------------------------------------
# Optional command-line test
# ---------------------------------------------------------

if __name__ == "__main__":

    import asyncio

    async def test():

        result = await ask(
            "What are the must-visit attractions in Singapore?"
        )

        print("\nANSWER:\n")
        print(result["answer"])

        print("\nTOOLS USED:\n")
        for event in result["tool_events"]:
            print(event)

        print("\nSOURCES:\n")
        for source in result["kb_sources"]:
            print(source)

    asyncio.run(test())