# BeeDoula 🐝

**An agentic RAG assistant for babysitters caring for infants (0–24 months).**

BeeDoula helps babysitters follow the parents' instructions and trusted infant-care guidance when the parents are unavailable. Parents provide the baby's profile, allergies, routines, emergency contacts, and house rules; the babysitter gets quick answers grounded in those notes and vetted sources.

> ⚠️ BeeDoula provides general care information, not diagnosis, treatment, or medical advice. In an emergency, call your local emergency number immediately and do not wait for BeeDoula.

## Certification Challenge

This project is a submission for the AI Engineering Certification Challenge.
📄 **[Written deliverables: docs/certification-challenge.md](docs/certification-challenge.md)**
🎥 **Demo video:** _coming soon_
🌐 **Live app:** _coming soon_

## Stack

| Component | Choice |
|---|---|
| LLM | OpenAI via LLM gateway |
| Orchestration | LangGraph |
| Tools | RAG retriever · Tavily web search · baby-profile memory |
| Embeddings / Vector DB | OpenAI `text-embedding-3-small` / Qdrant |
| Memory | LangGraph checkpointer (threads) + store (baby profile) |
| Monitoring / Evals | LangSmith / RAGAS |
| Frontend | Next.js + shadcn/ui, deployed on Vercel |
| Agent server | LangGraph server (Docker), deployed on Render |

## Local development

```bash
# Backend (from repo root)
uv sync
uv run langgraph dev          # dev server on :2024

# Frontend
cd frontend
npm install
npm run dev                   # http://localhost:3000
```

Copy `.env.example` to `.env` and fill in API keys.
