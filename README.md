# NestNote 🍼

**An agentic RAG assistant for babysitters and parents caring for infants (0–24 months).**

NestNote answers everyday infant-care questions — feeding, sleep, safety, milestones — grounded in vetted care guidelines and the family's own notes. It remembers each baby's profile (age, allergies, routines), searches the live web for current advisories and recalls, and runs in any browser on phone or laptop.

> ⚠️ NestNote is a care-information assistant, not a medical professional. For emergencies, call 911 or your pediatrician.

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
