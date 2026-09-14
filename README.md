# 🌏 Singapore AI Travel Planning Assistant

An AI-powered Singapore travel assistant built using **Streamlit, LangChain, Google Gemini, RAG, ChromaDB, and MCP tools**.

The application provides Singapore travel information from a curated knowledge base and uses MCP tools for **live weather forecasts and currency conversion**.

---

## 1. Features

* Singapore attractions and neighbourhood recommendations
* Transportation and practical travel information
* Food and local experiences
* Indoor and outdoor activity suggestions
* Multi-day itinerary planning
* Semantic search using RAG
* Source references for retrieved travel information
* Live weather forecast using MCP
* Currency conversion using MCP
* Weather-aware itinerary adjustment
* Multi-turn conversation support
* Graceful handling of tool/service failures

---

## 2. Architecture

```text
User
  │
  ▼
Streamlit UI
  │
  ▼
LangChain Agent + Google Gemini
  │
  ├──────────────► RAG
  │                 │
  │                 ▼
  │          Chroma Vector Store
  │                 │
  │                 ▼
  │        Singapore Knowledge Base
  │
  ├──────────────► Weather MCP
  │                 │
  │                 ▼
  │             Open-Meteo
  │
  └──────────────► Currency MCP
                    │
                    ▼
                 Frankfurter
  │
  ▼
Final Travel Response
```

---

## 3. Technology Stack

| Component       | Technology                         |
| --------------- | ---------------------------------- |
| UI              | Streamlit                          |
| LLM             | Google Gemini                      |
| Agent Framework | LangChain                          |
| RAG             | LangChain + ChromaDB               |
| Embeddings      | Hugging Face Sentence Transformers |
| Weather         | MCP + Open-Meteo                   |
| Currency        | MCP + Frankfurter                  |
| Language        | Python                             |
| Conversation    | Streamlit Session State            |

---

## 4. Project Structure

```text
singapore-travel-assistant/
│
├── app.py
├── requirements.txt
├── .env
├── .env.example
├── .gitignore
├── README.md
│
├── data/
│   └── singapore/
│       ├── wikivoyage.md
│       ├── visit_singapore_essentials.md
│       ├── visit_singapore_itinerary.md
│       └── visit_singapore_plan.md
│
├── rag/
│   ├── __init__.py
│   ├── ingest.py
│   └── retriever.py
│
├── mcp_servers/
│   ├── weather_server.py
│   └── currency_server.py
│
├── services/
│   ├── __init__.py
│   └── travel_agent.py
│
├── test/
│   ├── test_mcp_weather.py
│   └── test_mcp_currency.py
│
└── vectorstore/
```

---

## 5. Knowledge Base and RAG

The project contains curated Singapore travel information from multiple sources, including:

* Visit Singapore – Essential Singapore Travel Information
* Visit Singapore – Plan Your Trip
* Visit Singapore – 7 Days in Singapore Itinerary
* Wikivoyage Singapore Travel Guide

The RAG pipeline works as follows:

```text
Markdown Documents
       ↓
Document Chunking
       ↓
Hugging Face Embeddings
       ↓
ChromaDB
       ↓
Semantic Similarity Search
       ↓
Relevant Travel Context
       ↓
Gemini
       ↓
Final Answer
```

The `customerID`-style irrelevant metadata is not applicable here; only useful travel content and source metadata are stored.

Each retrieved document contains source information so that the application can display the knowledge-base references used in the response.

---

## 6. MCP Tools

### Weather MCP

Tool:

```text
get_weather_forecast
```

The weather server uses **Open-Meteo** to retrieve current/future daily weather information.

It provides:

* Date
* Maximum temperature
* Minimum temperature
* Rain probability
* Rainfall
* Weather code

The MCP server is started automatically by the application.

### Currency MCP

Tool:

```text
convert_currency
```

The currency server uses **Frankfurter** to retrieve exchange-rate information.

Example:

```text
Convert INR 50,000 to SGD
```

Example output:

```text
INR 50,000 is approximately SGD 670.39
```

---

## 7. Agent and Prompt Strategy

The LangChain agent decides which capability is required.

### Stable travel information

For questions such as:

```text
What are the must-visit attractions in Singapore?
```

the agent uses the RAG knowledge base.

### Current information

For questions such as:

```text
What is the weather in Singapore tomorrow?
```

the agent uses the Weather MCP tool.

For:

```text
Convert INR 50,000 to SGD.
```

the agent uses the Currency MCP tool.

### Combined scenario

For:

```text
Create a 3-day Singapore itinerary for next week and adjust it according to the weather forecast.
```

the application combines:

```text
RAG
 +
Weather MCP
 +
Gemini
```

The knowledge base provides destination information while the weather MCP provides current/future forecast data. Gemini then creates a weather-aware itinerary.

---

## 8. Multi-Turn Conversation

The application maintains conversation history using Streamlit session state.

For example:

```text
User:
Plan a 3-day Singapore trip.

User:
I am travelling with children.

User:
Make Day 2 more indoor.
```

The agent can use the previous conversation context when generating the next response.

---

## 9. Setup

### Step 1 – Install dependencies

Open PowerShell in the project folder:

```powershell
pip install -r requirements.txt
```

No virtual environment is required for this project.

### Step 2 – Configure Gemini

Create a `.env` file:

```env
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
GEMINI_MODEL=gemini-3.8-flash
```

Replace `YOUR_GEMINI_API_KEY` with your Google AI Studio API key.

---

## 10. Build the RAG Vector Store

Run:

```powershell
python rag\ingest.py
```

This will:

1. Read the Singapore Markdown documents.
2. Split them into chunks.
3. Generate embeddings.
4. Store the embeddings in ChromaDB.

The generated vector store is stored in:

```text
vectorstore/
```

---

## 11. Test MCP Servers

### Weather MCP

```powershell
python test\test_mcp_weather.py
```

Expected result:

```text
Available tools:
- get_weather_forecast

"ok": true
```

### Currency MCP

```powershell
python test\test_mcp_currency.py
```

Expected result:

```text
Available tools:
- convert_currency
```

The test should return a successful currency conversion.

---

## 12. Run the Application

Start Streamlit:

```powershell
streamlit run app.py
```

Open:

```text
http://localhost:8501
```

The application starts the MCP servers automatically when required, so the weather and currency servers do **not** need to be started manually.

---

## 13. Demo Questions

Use the following questions during evaluation.

### RAG

```text
What are the must-visit attractions in Singapore?
```

```text
Which neighbourhoods are good for cultural experiences?
```

```text
How can I travel around Singapore?
```

### Weather MCP

```text
What is the weather in Singapore tomorrow?
```

### Currency MCP

```text
Convert INR 50,000 to SGD.
```

### Combined RAG + MCP

```text
Create a three-day Singapore itinerary for next week and adjust it according to the weather forecast.
```

### Multi-Turn Conversation

```text
I am travelling with children. Make Day 2 more indoor.
```

---

## 14. Failure Handling

The application includes basic error handling for external services.

Examples include:

* Invalid weather dates
* Invalid forecast duration
* Location not found
* Weather API failure
* Currency API failure
* Missing knowledge base
* Missing Gemini API key
* MCP connection/tool errors

Instead of silently producing fabricated live information, the application reports the service failure.

---

## 15. Evaluation Mapping

| Requirement         | Implementation                        |
| ------------------- | ------------------------------------- |
| 3+ travel resources | 4 Singapore travel documents          |
| Semantic retrieval  | Hugging Face embeddings + ChromaDB    |
| Source references   | Source title and URL metadata         |
| LLM                 | Google Gemini                         |
| Agent framework     | LangChain                             |
| Weather MCP         | `get_weather_forecast`                |
| Currency MCP        | `convert_currency`                    |
| Combined RAG + MCP  | Weather-aware itinerary               |
| Multi-turn context  | Streamlit session state               |
| Tool selection      | LangChain agent                       |
| Failure handling    | Error handling in RAG/MCP/application |
| User interface      | Streamlit                             |

---

## 16. End-to-End Example

User:

```text
Create a 3-day Singapore itinerary for next week and adjust it according to weather forecast.
```

The application:

```text
1. Understands the user's request
          ↓
2. Retrieves relevant Singapore travel information
          ↓
3. Calls Weather MCP
          ↓
4. Receives forecast data
          ↓
5. Gemini combines travel knowledge + weather
          ↓
6. Generates a 3-day itinerary
          ↓
7. Places outdoor activities on better-weather days
          ↓
8. Moves activities indoors when rain is expected
          ↓
9. Shows knowledge-base sources
          ↓
10. Shows MCP tools used
```

This demonstrates the main objective of the project: **combining RAG-based stable knowledge with MCP-based live information in an AI travel assistant.**

---

## 17. Submission

The project can be submitted as a Git repository containing:

```text
Source Code
Knowledge Base
RAG Pipeline
MCP Servers
Tests
README
Requirements
Streamlit Application
```

Before submission, verify:

```powershell
python rag\ingest.py
python test\test_mcp_weather.py
python test\test_mcp_currency.py
streamlit run app.py
```

Then demonstrate the RAG, Weather MCP, Currency MCP, combined itinerary, and multi-turn conversation scenarios.
