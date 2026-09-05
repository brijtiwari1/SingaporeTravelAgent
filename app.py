import asyncio

import streamlit as st

from services.travel_agent import ask

st.set_page_config(page_title="Singapore Travel Assistant", page_icon="🌏", layout="wide")

st.title("🌏 Singapore Travel Planning Assistant")
st.caption("RAG for destination knowledge + MCP for live weather and currency")

if "chat" not in st.session_state:
    st.session_state.chat = []
if "history" not in st.session_state:
    st.session_state.history = []

with st.sidebar:
    st.header("Demo questions")
    st.markdown(
        """
- What are the must-visit attractions in Singapore?
- Which neighbourhoods are good for cultural experiences?
- How can I travel around Singapore?
- What is the weather in Singapore tomorrow?
- Convert INR 50,000 to SGD.
- Plan a 3-day Singapore trip and adjust it using the weather forecast.
- I am travelling with children. Make day 2 more indoor.
"""
    )
    if st.button("Clear conversation"):
        st.session_state.chat = []
        st.session_state.history = []
        st.rerun()

for item in st.session_state.chat:
    with st.chat_message(item["role"]):
        st.markdown(item["content"])

question = st.chat_input("Ask about Singapore, weather, currency, or a trip plan...")

if question:
    st.session_state.chat.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Planning..."):
            try:
                result = asyncio.run(ask(question, st.session_state.history))
                answer = result["answer"]
                st.markdown(answer)

                if result["kb_sources"]:
                    st.markdown("### Knowledge-base sources")
                    for source in result["kb_sources"]:
                        title = source["title"]
                        url = source["url"]
                        st.markdown(f"- [{title}]({url})")

                if result["tool_events"]:
                    st.markdown("### MCP tools used")
                    for event in result["tool_events"]:
                        tool_name = event["tool"]
                        if tool_name in {"get_weather_forecast", "convert_currency"}:
                            st.markdown(f"- `{tool_name}`")

                st.session_state.history = result["messages"]
                st.session_state.chat.append({"role": "assistant", "content": answer})
            except Exception as exc:
                st.error(f"Application error: {exc}")
