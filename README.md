# Singapore Travel Planning Assistant

An AI travel-planning assistant for the assignment: **RAG for stable destination knowledge + MCP tools for current weather and currency**.

## Architecture

```text
Streamlit UI
    |
    v
LangChain Agent
    |
    +--> search_travel_knowledge --> Chroma --> Singapore KB
    |
    +--> get_weather_forecast --> Weather MCP --> Open-Meteo
    |
    +--> convert_currency --> Currency MCP --> Frankfurter
    |
    v
LLM response with sources + MCP/tool information
```

LangChain's current `create_agent` supports tool-using agents, and `langchain-mcp-adapters` loads MCP tools into LangChain agents. The MCP Python SDK supports standard transports including stdio and Streamable HTTP.

## Why MCP is used

Weather and exchange rates are time-sensitive, so they are retrieved at request time through MCP tools. Destination facts are kept in the local knowledge base and retrieved with semantic search. The LLM is instructed not to invent either source.

## Project structure

```text
singapore-travel-assistant/
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── data/
│   └── singapore/
│       ├── wikivoyage.md
│       ├── visit_singapore_essentials.md
│       ├── visit_singapore_itinerary.md
│       └── visit_singapore_plan.md
├── rag/
│   ├── ingest.py
│   └── retriever.py
├── mcp_servers/
│   ├── weather_server.py
│   └── currency_server.py
├── services/
│   └── travel_agent.py
└── vectorstore/
```

## 1. Prerequisites

Recommended for Windows: **Python 3.11 or 3.12**. Avoid using Python 3.14 for this project if possible because the ML/LLM ecosystem can lag behind the newest Python release.

You need an OpenAI API key for the sample implementation. Put it in `.env`; never commit `.env`.

## 2. Create the environment

PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks activation, use Command Prompt:

```cmd
.venv\Scripts\activate
```

## 3. Configure the LLM

Copy `.env.example` to `.env`:

```text
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4.1-mini
```

The project does not put the key in source code.

## 4. Build the knowledge base

The four files in `data/singapore` are starter metadata files. Replace their placeholder text with content that you are permitted to ingest/redistribute from the listed public sources. Keep the `# Title` and `Source URL:` lines because they become citation metadata.

Then run:

```powershell
python rag/ingest.py
```

The script:

1. loads the Markdown files;
2. creates meaningful overlapping chunks;
3. creates normalized sentence-transformer embeddings;
4. stores vectors in Chroma;
5. preserves source title and URL metadata.

## 5. Run the application

```powershell
streamlit run app.py
```

Open the local Streamlit URL shown in the terminal.

## 6. Test the MCP servers independently

The MCP servers use stdio, so the LangChain MCP client starts them automatically. You normally do not need separate terminals.

For debugging, the MCP Inspector can be used with the server scripts if your MCP CLI/Node environment is installed.

## 7. Required demo questions

### RAG only

> What are the must-visit attractions in Singapore?

Expected behavior: the agent calls `search_travel_knowledge` and returns knowledge-base sources.

### Weather MCP only

> What is the weather in Singapore tomorrow?

Expected behavior: the agent calls `get_weather_forecast`. The answer should identify that the weather came from MCP/current data.

### Currency MCP only

> Convert INR 50,000 to SGD.

Expected behavior: the agent calls `convert_currency` and reports the returned rate/value and date when available.

### Combined RAG + MCP

> Plan a three-day Singapore itinerary for next week and adjust the activities according to the weather forecast.

Expected behavior:

1. retrieve attractions, itinerary ideas, indoor/outdoor options and transport guidance from the KB;
2. call the weather MCP tool;
3. combine both sources;
4. produce a day-by-day itinerary;
5. replace or reorder outdoor activities when rain is forecast;
6. identify KB sources and MCP usage.

### Multi-turn memory

> I am travelling to Singapore with my family.

Then:

> Plan three days.

Then:

> Make day 2 more indoor.

The Streamlit app replays user/assistant history so the later questions retain the trip context.

## Prompt strategy

The system prompt separates three evidence types:

- **Knowledge base:** stable destination facts and source references.
- **Current MCP information:** weather and currency returned at request time.
- **AI recommendation:** the model's synthesis, prioritization and itinerary suggestions.

The prompt explicitly says to call the relevant source/tool, never fabricate missing facts, and report tool failures instead of inventing current values.

## Failure handling

- Missing vector store: the application reports that `python rag/ingest.py` must be run.
- Knowledge retrieval failure: the RAG tool returns a visible error rather than fake facts.
- Weather API failure: the MCP tool returns `ok=false` and the agent is instructed to report that current weather could not be retrieved.
- Currency API failure: same behavior; no exchange rate is invented.

## Knowledge-base sources

1. Wikivoyage Singapore Travel Guide
   https://en.wikivoyage.org/wiki/Singapore
2. Visit Singapore - Essential Singapore Travel Information
   https://www.visitsingapore.com/travel-tips/essential-travel-information/
3. Visit Singapore - 7 Days in Singapore
   https://www.visitsingapore.com/content/visitsingapore/en/travel-tips/travelling-to-singapore/itineraries/7-days-in-singapore
4. Visit Singapore - Plan Your Trip
   https://www.visitsingapore.com/mice/en/tools-and-resources/plan-your-trip/

Review each source's current terms before redistributing copied content. For a submission repository, it is safer to include your own permitted extracts or clear instructions for obtaining the source material rather than committing material you are not licensed to redistribute.

## MCP tools

### Weather

`get_weather_forecast(location, start_date, days)` uses Open-Meteo forecast data through the weather MCP server.

### Currency

`convert_currency(amount, from_currency, to_currency)` uses Frankfurter's latest exchange-rate endpoint through the currency MCP server.

## Assignment acceptance mapping

| Requirement | Implementation |
|---|---|
| 3+ travel resources | Four Singapore sources listed above |
| Meaningful chunks | `RecursiveCharacterTextSplitter` |
| Embeddings | `all-mpnet-base-v2` |
| Vector store | Chroma |
| Grounded answers | RAG tool + system prompt |
| Source references | `source_title` and `source_url` metadata |
| Weather MCP | `get_weather_forecast` |
| Currency MCP | `convert_currency` |
| Tool selection | LangChain agent |
| Combined response | RAG + weather MCP |
| Multi-turn context | Streamlit history replay |
| Missing knowledge | Explicit prompt rule + retrieval errors |
| MCP failures | `ok=false` tool results + no-fabrication rule |
| UI | Streamlit |

## Important implementation note

The starter KB files intentionally do not reproduce third-party pages. Populate them with content you are allowed to use. This makes the repository safer to distribute and lets you document exactly what source material was ingested.
