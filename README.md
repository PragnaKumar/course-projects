# 📚 Moodreads
### AI-Powered Mood-Aware Book Recommendation System

> Tell us how you feel — we'll find the perfect read.

Moodreads is an agent-based reading recommendation system built with LangGraph, the Model Context Protocol (MCP), and locally running large language models via Ollama. It recommends fiction, research papers, and textbooks based on your current mood or information need — explained in natural language, with direct links to every result.

---

## ✨ Features

- 🎭 **Mood inference** — describe how you feel in plain English, the system figures out the rest
- 📖 **Fiction & Leisure** — mood-mapped book recommendations via Google Books
- 📄 **Research Papers** — searches 6 sources simultaneously (ArXiv, PubMed, bioRxiv, medRxiv, IEEE Xplore)
- 📘 **Textbooks** — level-aware academic textbook recommendations
- 🔗 **Always includes links** — every recommendation has a direct URL
- 💾 **Persistent memory** — conversation history and mood preferences saved across sessions
- 🏗️ **MCP architecture** — Google Books, ArXiv and IEEE Xplore exposed as independent FastMCP servers

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Agent Framework | LangGraph |
| LLM | Ollama + qwen2.5:7b |
| MCP Servers | FastMCP + uvicorn |
| UI | Streamlit |
| Memory | SqliteSaver + SQLite |
| APIs | Google Books · ArXiv  · PubMed · bioRxiv · IEEE Xplore |

---

## 🦙 Installing Ollama

Ollama is required to run the LLM locally.

**Mac**
```bash
brew install ollama
```

**Linux**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**Windows**

Download the installer from [ollama.com](https://ollama.com) and run it.

After installing, pull the model:
```bash
ollama pull qwen2.5:7b
```

---

## 🚀 Running Locally

### Prerequisites
- Python 3.11+
- Ollama installed (see above)

### Setup

```bash
# 1. Clone the repo
git clone https://github.com/PragnaKumar/course-projects.git
cd course-projects
git checkout moodreads

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Edit .env and add your API keys

# 5. Start Ollama
ollama serve

# 6. In a new terminal — start the MCP servers
python mcp_servers/arxiv_server.py &
python mcp_servers/google_books_server.py &
python mcp_servers/ieee_server.py &

# 7. Run the app
streamlit run app.py
```

---

## 🔑 Environment Variables

Copy `.env.example` to `.env` and fill in your keys:

```bash
cp .env.example .env
```

| Variable | Required | Where to get it |
|---|---|---|
| `GOOGLE_BOOKS_API_KEY` | Yes | [Google Cloud Console](https://console.cloud.google.com) |
| `IEEE_API_KEY` | Yes | [developer.ieee.org](https://developer.ieee.org) |
| `OLLAMA_BASE_URL` | No | Default: `http://localhost:11434` |
| `OLLAMA_MODEL` | No | Default: `qwen2.5:7b` |

---

## 🏗️ Project Structure

```
moodreads/
├── agents/
│   ├── leisure_agent.py       # Mood-based fiction recommendations
│   ├── research_agent.py      # Multi-source academic paper search
│   └── tb_agent.py            # Textbook recommendations
├── graph/
│   └── router.py              # LangGraph router
├── logic/
│   └── mood_wrapper.py        # Mood taxonomy (18 moods → search hints)
├── mcp_servers/
│   ├── arxiv_server.py        # ArXiv MCP server (:8001)
│   ├── google_books_server.py # Google Books MCP server (:8002)
│   └── ieee_server.py         # IEEE Xplore MCP server (:8003)
├── memory/
│   ├── conversation.py        # SqliteSaver checkpointer
│   └── preferences.py         # User preference store
├── models/
│   └── llm.py                 # Ollama LLM factory
├── tools/
│   ├── arxiv.py               # MCP client + direct fallback
│   ├── google_books.py        # MCP client + direct fallback
│   ├── ieee.py                # MCP client + direct fallback
│   ├── pubmed.py              # PubMed direct client
│   └── biorxiv.py             # bioRxiv + medRxiv client
├── ui/
│   ├── styles.py              # CSS + shared helpers
│   ├── landing.py             # Landing page
│   ├── chat_base.py           # Shared chat logic
│   ├── leisure_page.py        # Fiction chat page
│   ├── research_page.py       # Research chat page
│   └── textbook_page.py       # Textbook chat page
├── app.py                     # Entry point
├── requirements.txt
└── .env.example
```

---

## 💬 Example Prompts

**Fiction**
- *I'm feeling anxious, suggest something calming*
- *I want a fast-paced thriller for the weekend*
- *Something cozy for a lonely evening*

**Research**
- *Latest papers on large language models 2024*
- *Survey papers on reinforcement learning*
- *Research on transformer attention mechanisms*

**Textbooks**
- *Beginner textbook for linear algebra*
- *Graduate level deep learning book*
- *Best book to learn Python from scratch*

---

## 🎓 Academic Context

Built as a directed study project at **Wayne State University**, April 2026.