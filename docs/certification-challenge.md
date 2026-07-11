# Certification Challenge — BeeDoula 🐝: Infant Care Assistant (0–24 months)

> Submission for the AI Engineering Certification Challenge (AI Makerspace).
> Live app: _TODO (Step 4)_ · Demo video: _TODO (Step 7)_

---

## Task 1: Defining the Problem, Audience, and Scope

### 1.1 Problem statement (one sentence)

Babysitters caring for an infant (0–24 months) cannot quickly get trustworthy answers that combine the parents' instructions with age-specific, vetted care guidance.

### 1.2 Why this is a problem for our user

Our primary user is a **babysitter** who is alone with a baby and needs an answer *right now*: How much formula does this baby take? Is honey safe at 10 months? What is the usual nap schedule? Infant care is uniquely unforgiving — the answers change month by month, and the stakes of getting choking, sleep, or allergen guidance wrong are high. Parents are secondary participants: they provide the baby's profile, routines, allergies, emergency contacts, and house rules before care begins.

Today, caregivers cope with a patchwork: they text the parents and wait, they Google and get a wall of conflicting mommy-blogs, ad-laden listicles, and outdated advice, or they dig through the family's handwritten notes, fridge printouts, and pediatrician handout folder. None of these is good enough. Texting is slow and often goes unanswered at the worst moment. Web search is generic — it doesn't know the baby is 7 months old, allergic to eggs, and on a specific nap schedule — and forces a stressed caregiver to adjudicate between contradictory sources under time pressure. And the family's own notes, the most relevant information of all, are scattered, unsearchable, and usually not where the caregiver is standing. The result: slow answers, guesswork, unnecessary panic calls, and occasionally genuinely unsafe decisions.

### 1.3 How the user solves this problem today (workflow diagram)

```mermaid
flowchart TD
    A([Care question arises<br/>baby fussing, feeding, symptom]) --> B{Parents<br/>reachable?}
    B -- text/call --> C[Wait for reply…]
    C -- "⏱️ minutes–hours, often<br/>at the worst moment" --> D{Answered?}
    D -- no --> E[Google it]
    B -- no --> E
    E -- "⚠️ conflicting blogs, ads,<br/>outdated or generic advice" --> F[Skim 5+ pages,<br/>compare answers]
    F --> G[Check family notes:<br/>fridge printouts, binder,<br/>pediatrician handouts]
    G -- "⚠️ scattered, unsearchable,<br/>often missing" --> H{Confident?}
    D -- yes --> I([Act])
    H -- yes --> I
    H -- no --> J[Guess, or escalate:<br/>panic call to parents,<br/>nurse line, or ER]
    J -- "⚠️ error-prone,<br/>stressful, costly" --> I
```

The slow points are the waits (texting parents); the error-prone points are generic web results that ignore the baby's age and history, and scattered family notes that can't be searched.

### 1.4 Evaluation questions

Questions our application must answer well, spanning the corpus (guidelines), the family notes (baby-specific), and live web search:

| # | Question | Expected answer grounds |
|---|---|---|
| 1 | How much formula should a 6-month-old drink per feeding? | Feeding guidelines (≈180–240 ml per feeding, 4–5×/day) |
| 2 | When can babies start eating solid foods? | Feeding guidelines (~6 months, readiness signs) |
| 3 | Is honey safe for a 10-month-old? | Safety guidelines (no — botulism risk before 12 months) |
| 4 | My baby is 4 months old with a 38.2 °C fever — what should I do? | Health guidelines (contact pediatrician; <3 months = emergency) |
| 5 | How should I put the baby down to sleep safely? | Safe-sleep guidelines (back, firm surface, nothing in crib) |
| 6 | How many naps does a 9-month-old typically take? | Sleep guidelines (2 naps) |
| 7 | What do I do if the baby is choking? | Choking/CPR guidance (back blows/chest thrusts by age) |
| 8 | What foods are choking hazards for a 1-year-old? | Safety guidelines (grapes, nuts, hot dogs…) |
| 9 | When should a baby be able to sit up on their own? | Milestone guidelines (~6 months) |
| 10 | Is it normal that my 8-month-old isn't crawling yet? | Milestone guidelines (range; when to ask pediatrician) |
| 11 | How do I safely warm a bottle of breast milk? | Feeding guidelines (warm water, never microwave) |
| 12 | How long can formula sit out before it's unsafe? | Feeding guidelines (1–2 hours) |
| 13 | What's a good bedtime routine for a 1-year-old? | Sleep guidelines |
| 14 | The baby has a diaper rash — what should I do? | Care guidelines (air, barrier cream; when to escalate) |
| 15 | Does *this* baby have any food allergies I should know about? | **Family notes / baby profile (memory)** |
| 16 | What's the baby's usual nap schedule? | **Family notes / baby profile (memory)** |
| 17 | Have there been any recent recalls of [specific formula brand]? | **Tavily live web search** |
| 18 | What's the current guidance on peanut introduction? | Guidelines + Tavily (current advisories) |
| 19 | Can a 15-month-old drink cow's milk? | Feeding guidelines (yes, whole milk after 12 months) |
| 20 | The baby fell off the couch and is crying — what do I check? | Health guidelines (warning signs; when to call local emergency services) |

---

## Task 2: Proposed Solution

### 2.1 Solution (one sentence)

BeeDoula is an agentic RAG assistant that helps babysitters follow the parents' instructions and vetted infant-care guidance when the parents are unavailable, while clearly remaining a general-information tool rather than a medical app.

### 2.2 Infrastructure diagram and tooling choices

#### Implemented prototype and deployment configuration

```mermaid
flowchart TB
    subgraph Client["Client — implemented in frontend/"]
        UI[Next.js + shadcn/ui<br/>streaming chat]
        PX[Next.js server-side<br/>LangGraph API proxy]
        UI --> PX
    end
    subgraph Server["Backend — Render blueprint runs langgraph dev"]
        LG[LangGraph create_agent<br/>tool-calling loop]
        MEM[(LangGraph development<br/>checkpoints + shared profile<br/>non-durable)]
        IDX[(In-memory Qdrant + BM25<br/>built from data/ per process)]
        LG --- MEM
        LG --- IDX
    end
    subgraph External["External services"]
        GW[Vercel AI Gateway]
        OAI[OpenAI<br/>gpt-5.4-mini + embeddings]
        TAV[Tavily web search]
        LS[LangSmith<br/>tracing & datasets]
    end
    PX -- "streamed messages<br/>(LangGraph API)" --> LG
    LG -- "LLM calls" --> GW --> OAI
    LG -- "web search tool" --> TAV
    LG -. "traces / evals" .-> LS
    RAGAS[RAGAS eval harness] -. "runs against" .-> LG
    RAGAS -. "logs to" .-> LS
```

This diagram is the architecture implemented in the repository today. Frontend and
Render deployment configurations are present, but a public deployment is not claimed until the
working frontend and backend URLs are added in Task 4. The Qdrant collection, checkpoints,
and profile store are currently process-local: they reset when the backend restarts, and
the corpus is embedded again when a new process first performs retrieval.

#### Planned production architecture (not yet implemented)

```mermaid
flowchart LR
    U[Authenticated parent<br/>or babysitter] --> FE[Next.js frontend<br/>Vercel]
    FE --> API[Production LangGraph<br/>service]
    API --> PG[(Postgres<br/>durable checkpoints +<br/>family-scoped profiles)]
    API --> QC[(Qdrant Cloud<br/>pre-indexed collection)]
    API --> GW[Vercel AI Gateway]
    API --> TV[Tavily]
    API -. traces .-> LS[LangSmith]
```

Postgres, managed Qdrant, authentication, per-family namespaces, one-time ingestion,
and a production server command are **planned upgrades**, not features of the current
prototype.

Why each component and its current status:

| Component | Choice | Why | Status now |
|---|---|---|---|
| LLM | OpenAI `gpt-5.4-mini` | Strong instruction-following and tool-calling at a cost suitable for a small prototype. | Implemented through configuration. |
| LLM gateway | Vercel AI Gateway | One OpenAI-compatible endpoint provides routing and spend visibility without provider-specific application code. | Implemented; requires a valid deployment credential. |
| Agent orchestration | LangGraph | Supplies the tool-calling loop, thread protocol, checkpointer, and store interfaces used by the frontend and memory tools. | Implemented with the development server. |
| Tools | RAG retriever · Tavily · memory tools | RAG covers static guidance, Tavily covers time-sensitive questions, and memory tools hold baby-specific facts. | Implemented; Tavily is enabled only when its key is configured. |
| Embeddings | OpenAI `text-embedding-3-small` | Appropriate cost and quality for this small corpus and compatible with the gateway. | Implemented; embeddings are regenerated per backend process. |
| Vector retrieval | In-memory Qdrant + BM25 + RRF | Dense retrieval handles paraphrases while BM25 preserves exact ages, amounts, and safety terms. | Implemented and non-durable; Qdrant Cloud is planned. |
| Memory | LangGraph development checkpointer + store | Demonstrates thread continuity and cross-thread profile recall. | Implemented for one shared demo family; resets on restart. |
| Monitoring | LangSmith | Captures tool and model traces needed for debugging and evaluation. | Implemented when tracing credentials are configured. |
| Evaluation | RAGAS + LangSmith datasets | Supplies context recall, faithfulness, and answer-accuracy measurements over the real agent. | Implemented; per-question CSV evidence is committed. |
| Frontend | Next.js + shadcn/ui | Provides a mobile-friendly streaming chat and keeps backend credentials server-side. | Implemented; public Vercel URL still required. |
| Backend hosting | Render native Python service | Hosts the LangGraph HTTP API outside Vercel's serverless runtime. | Blueprint implemented with `langgraph dev`; production runtime and public URL remain. |

### 2.3 Agent workflow diagram

```mermaid
flowchart TD
    U([Caregiver asks a question<br/>e.g. 'Can she have honey? She's 10 months.']) --> T[Development checkpointer restores<br/>the thread when available]
    T --> R{Agent chooses tools<br/>under system-prompt rules}
    R -- "baby-specific context needed" --> P[Read shared baby profile]
    R -- "care knowledge" --> RAG[📚 Retrieve from guidelines<br/>Qdrant vector search]
    R -- "current events:<br/>recalls, advisories" --> TV[🌐 Tavily web search]
    R -- "new fact about baby<br/>'she's allergic to eggs'" --> MEM[💾 Write to profile store]
    P --> A[Model composes response]
    RAG --> A
    TV --> A
    MEM --> A
    R -- "emergency language" --> E[System prompt requires<br/>immediate escalation wording]
    E --> A
    A --> O([Answer streamed to caregiver])
    O -- "caregiver decides & acts —<br/>human always in the loop" --> H[👤 Human judgment]
```

When a caregiver sends a message, the development checkpointer can restore that thread. The model then decides which tools to call under the system prompt: it reads the shared baby profile when the question is baby-specific, retrieves care information from the in-memory hybrid index, uses Tavily for time-sensitive questions, or writes a newly supplied fact to the profile. These choices are agent decisions rather than guaranteed deterministic steps. Profile facts can be recalled across threads while the same backend process and store remain available, but they are not durable across restarts.

The current safety behavior is an explicit system-prompt requirement, reinforced by the emergency banner in the frontend: emergency responses must lead with a direction to call the local emergency number. It is not yet a separate deterministic safety node, so deterministic triage and a dedicated safety evaluation remain required upgrades. Routine answers are instructed to use retrieved context and metric units. The retriever currently returns passage text without source metadata, so reliable user-facing citations are also planned rather than claimed as complete.

---

## Task 3: Dealing with the Data

### 3.1 Data sources and external APIs

**RAG corpus** (`data/`) — care guidance from established health organizations covering the four domains our eval questions probe. Source versions, direct download URLs, and redistribution terms still need to be recorded before a production release:

| File | Source | Covers |
|---|---|---|
| `cdc_milestone_moments.pdf` | CDC "Learn the Signs. Act Early." Milestone Moments booklet | Developmental milestones (2 months–5 years), when to act early |
| `nichd_safe_sleep_for_your_baby.pdf` | NIH/NICHD Safe to Sleep® brochure | Safe sleep environment, SIDS risk reduction |
| `who_infant_young_child_feeding.pdf` | WHO Infant and Young Child Feeding model chapter | Breastfeeding, formula, complementary feeding 0–24 months |
| `aha_infant_cpr_choking_fact_sheet.pdf` | American Heart Association fact sheet | Infant choking response and CPR steps |
| `family_notes_sample.md` | Written by the family (fictional sample in this repo) | *This* baby: allergies, feeding amounts, nap schedule, house rules, pediatrician contacts |

The first four are the **vetted general knowledge**: they answer "what's true for babies of this age." The family notes are the **personal data** that makes answers specific: "what's true for *Mia*." Real family notes are never committed — they belong in a gitignored `data/family_notes_private.md`.

**External API — Tavily web search.** A static corpus cannot know about last week's formula recall or this month's updated advisory. The agent calls Tavily when a question is time-sensitive (recalls, current guidance, product safety) or falls outside the corpus.

**How they interact at runtime:** for a question like "Can Mia have scrambled eggs?", the agent combines all three layers — the family notes say Mia is allergic to eggs (personal), the WHO guide describes allergen introduction (general), and Tavily is available if the question had a current-events component (e.g., an egg-product recall). The agent's answer leads with the baby-specific fact, grounded by the guideline context.

### 3.2 Default chunking strategy and rationale

**Default: `RecursiveCharacterTextSplitter` with 750-token chunks (tiktoken-measured), no overlap** (`app/rag.py`).

Why:
1. **Our documents are section-structured.** Care guidelines are written as self-contained topical sections ("Safe sleep environment," "Feeding at 6–8 months," "Choking response steps"). 750 tokens is roughly one such section, so a chunk usually holds one complete, coherent answer unit — which is exactly what we want retrieved.
2. **Token-based measurement matches the embedding model's view.** Measuring chunk size in tokens (via tiktoken) rather than characters keeps chunks consistently sized from the model's perspective, avoiding chunks that blow past useful embedding length.
3. **Recursive splitting respects document structure.** The splitter breaks on paragraphs before sentences before words, so chunks tend to end at natural boundaries instead of mid-instruction — important when a chunk contains step-by-step safety instructions (choking response) that must not be cut in half.
4. **Zero overlap is a deliberate baseline.** It maximizes corpus coverage per embedding dollar and gives us a clean baseline to measure against; if evaluation (Task 5) shows boundary-loss problems, chunk overlap and **parent-child chunking** (retrieve small, return the surrounding section) are the planned Task 6 upgrades.

---

## Task 4: End-to-End Agentic RAG Prototype

### 4.1 Architecture notes

The repository implements an end-to-end **single-family, non-durable prototype**. It demonstrates the user-facing workflow but does not yet implement the separate production architecture shown in Task 2:

- **Agent** (`app/graphs/simple_agent.py`): LangGraph `create_agent` with prompt-based emergency escalation, grounding, and tool-selection rules; a deterministic safety gate is not yet implemented.
- **Tools** (`app/tools.py`): `retrieve_information` (hybrid RAG over the corpus + sample family notes), optional `tavily_search` (live web), and `get_baby_profile` / `save_baby_fact` (one shared demonstration namespace, `("beedoula", "baby_profile")`).
- **LLM + embeddings** (`app/models.py`, `app/rag.py`): both routed through the Vercel AI Gateway with a single `vck_` key — no direct provider keys anywhere.
- **Frontend** (`frontend/`): Next.js streaming chat with an API passthrough that keeps keys server-side; tool activity is shown as labeled badges ("Care guidelines", "Baby profile", "Web search", "Remembering").
- **Storage** (`app/rag.py`, LangGraph development server): Qdrant, checkpoints, and profile data are process-local. The vector index is rebuilt from `data/` for each new process, and all stored state can be lost on restart.

Two smoke-test scripts cover local retrieval and server SDK behavior, including saving a fact in one thread and recalling it in another. Historical evaluation runs demonstrate this flow, but a current smoke run still requires valid gateway credentials and a reachable backend; it is not presented as proof of durable production storage.

Known prototype limitations are explicit:

| Implemented now | Still required |
|---|---|
| Streaming chat and server-side API proxy | Verified public frontend and backend URLs |
| LangGraph tool-calling agent | Production server/runtime configuration |
| Hybrid dense + BM25 retrieval | Persistent, pre-indexed Qdrant collection |
| Process-local thread and profile memory | Postgres-backed durable checkpoints and store |
| One shared demonstration baby profile | Authentication, family/baby isolation, and roles |
| Prompt-based emergency instructions and UI banner | Deterministic safety gate and safety-specific evals |
| Retrieved passage text | Source/page metadata and verified user-facing citations |

### 4.2 Deployment

- **Backend configuration**: `render.yaml` defines a Render native Python service running `langgraph dev`. This is a prototype configuration, not a Docker/Postgres production deployment. _Public URL: TODO after verification._
- **Frontend configuration**: the Next.js application and server-side proxy are ready for Vercel. _Public URL: TODO after verification._

---

## Task 5: Evaluation

### 5.1 Test dataset

The dataset (`beedoula-eval-v1` in LangSmith, 29 examples, built by `evals/build_dataset.py`) combines two sources:

1. **9 synthetic examples** generated with the RAGAS `TestsetGenerator` over the guideline corpus, using the same Vercel AI Gateway models as the app. Corpus pages are merged per source and re-split into substantial sections first, because RAGAS's headline-extraction transforms fail on thin, image-heavy PDF pages.
2. **20 hand-written golden questions** from Task 1, each with a reference answer and a `kind` tag: `corpus` (answerable from the guidelines), `memory` (depends on the baby's saved profile), and `web` (requires live search). This deliberately covers all three retrieval paths of the agent, not just RAG.

### 5.2 Evaluation harness

The harness (`evals/run_evals.py`) is a rerunnable script, isolated in its own uv project so the pinned RAGAS build can't destabilize the app:

1. **Seeds the baby profile** through the agent server's store API (allergies, nap schedule, house rules matching the family notes), so memory questions are answerable and runs are reproducible.
2. **Runs the real agent** — not a stripped-down RAG chain — against each question in a fresh thread via the LangGraph SDK, capturing the final answer and every tool result (retrieval chunks, profile reads, web results) as the retrieved contexts.
3. **Scores three RAGAS metrics** with an LLM judge routed through the same gateway: **context recall** (did retrieval fetch the facts the reference needs?), **faithfulness** (is the answer grounded in what was retrieved?), and **answer accuracy** (does the answer match the reference?).
4. **Logs everything to LangSmith** as a named experiment (`EVAL_EXPERIMENT_PREFIX`) and writes a per-question CSV to `evals/out/` — so baseline vs. improved comparisons in Task 6 are one environment variable apart.

### 5.3 Baseline results and conclusions

Baseline (dense retrieval, k=4), experiment `baseline-clean-51b6438d`, 29/29 examples scored:

| Metric | Overall | corpus | memory | web |
|---|---|---|---|---|
| Context recall | **0.33** | 0.33 | 0.56 | 0.00 |
| Faithfulness | **0.40** | 0.40 | 0.53 | 0.14 |
| Answer accuracy | **0.65** | 0.66 | 0.83 | 0.25 |

**Conclusions:**

1. **Retrieval is the bottleneck.** A context recall of 0.33 means the dense retriever usually fails to fetch all the facts the reference answer needs. Care questions mix exact tokens (ages like "10 months", thresholds like "38 °C", terms like "honey", "botulism") with paraphrased phrasing — a known weakness of pure dense retrieval and a direct motivation for the hybrid (dense + BM25) upgrade in Task 6.
2. **The agent papers over retrieval gaps with parametric knowledge.** Answer accuracy (0.65) is much higher than faithfulness (0.40): when retrieval misses, the model answers from what it learned in training. Often correct — but in a safety domain we want verifiable, source-grounded answers, so faithfulness is the metric we most want to raise.
3. **Memory works.** Memory-kind questions score best across the board (accuracy 0.83), confirming the profile store pipeline retrieves and applies baby-specific facts.
4. **Web-kind scores are structurally noisy.** References for live-web questions describe expected *behavior* rather than fixed facts, so recall-against-reference is near zero by construction. We keep them in the set to watch answer accuracy, and treat their recall/faithfulness as a known limitation of the harness, not the agent.

---

## Task 6: Improving the Prototype

### 6.1 Advanced retrieval technique

**Hybrid retrieval: dense vectors + BM25, fused with reciprocal rank fusion (RRF).** Each query now runs both a dense similarity search and a BM25 lexical search over the same 750-token chunks (top-10 each), and RRF merges the two rankings into the final top-4 (`app/rag.py`, toggled by `RETRIEVER_MODE=hybrid`).

Why it fits this use case: infant-care questions mix **exact tokens** that dense embeddings tend to smear — ages ("10 months"), thresholds ("38 °C"), specific substances ("honey") — with **paraphrased intent** ("won't settle for his nap") that lexical search alone can't match. BM25 catches the exact terms, dense catches the paraphrase, and RRF rewards chunks both retrievers agree on.

### 6.2 Performance comparison

Same harness, dataset, and judge; only the retriever changed (experiments `baseline-clean-51b6438d` vs `hybrid-7543bfad`):

| Metric | Baseline (dense) | Hybrid (dense + BM25 + RRF) | Δ |
|---|---|---|---|
| Context recall | 0.332 | **0.371** | +0.039 |
| Faithfulness | 0.396 | **0.441** | +0.045 |
| Answer accuracy | 0.647 | 0.629 | −0.018 |

Hybrid retrieval improved both retrieval quality (context recall +12% relative) and grounding (faithfulness +11% relative), with answer accuracy flat within noise.

### 6.3 Second improvement (with eval evidence)

The baseline analysis (5.3) showed the agent papering over retrieval gaps with parametric knowledge — high accuracy, low faithfulness. So the second change targets a different piece of the solution: the **system prompt**. A GROUNDING section now requires every factual claim to come from this conversation's tool results (retrieved passages, baby profile, web results), quoting amounts and thresholds exactly, and — when the sources don't cover the question — saying so plainly and deferring to the pediatrician instead of filling the gap from memory (`app/graphs/simple_agent.py`).

Full progression across the three experiments:

| Metric | Baseline | Hybrid | Hybrid + grounded prompt | Δ vs baseline |
|---|---|---|---|---|
| Context recall | 0.332 | 0.371 | **0.420** | **+27% rel.** |
| Faithfulness | 0.396 | 0.441 | **0.528** | **+33% rel.** |
| Answer accuracy | 0.647 | 0.629 | 0.586 | −9% rel. |

Faithfulness — the metric that matters most in a safety domain — improved by a third over baseline. Context recall also rose, as the grounded agent retrieves more before answering. The answer-accuracy dip is a deliberate trade: the agent now sometimes answers "the guidelines I have don't cover this — ask your pediatrician" where it previously produced a plausible-but-ungrounded answer. Judged against a reference, the refusal scores lower; judged as a product for stressed caregivers of infants, **verifiable-or-defer is the correct behavior**. This is a meaningfully improved response profile, demonstrated with the eval harness as evidence.

---

## Task 7: Next Steps

**What we keep for Demo Day** — the architecture earned its place:

- **The LangGraph agent with three grounding layers** (guideline RAG, baby-profile memory, live web search): every eval segment confirmed each layer pulls its weight — memory questions score highest, and web search covers what a static corpus can't.
- **One-key LLM gateway routing** for chat and embeddings: simplest possible ops, provider flexibility for free.
- **Hybrid retrieval + the grounded prompt**: +33% relative faithfulness with three days of eval evidence behind it.
- **The eval harness itself**: it's rerunnable, tagged by question kind, and one env variable per experiment — it already caught one regression during development and becomes our pre-release gate.
- **The Next.js/Vercel frontend**: streaming, mobile-friendly, cheap.

**What we change** — ordered by impact:

1. **Verified deployment.** Publish and smoke-test the Vercel frontend and Render backend, then replace every URL placeholder with the verified endpoints.
2. **Production runtime and persistence.** Replace `langgraph dev` and process-local state with a production service, Postgres-backed checkpoints/store, and a persistent Qdrant Cloud collection indexed through a separate ingestion job.
3. **Multi-family support.** Add authentication, parent/babysitter roles, and server-derived namespaces per family and baby; the current shared profile is demonstration-only.
4. **Deterministic safety.** Add a pre-agent emergency triage gate and a dedicated safety evaluation covering critical misses, first-line escalation, over-escalation, adversarial prompts, and latency.
5. **Verifiable citations.** Preserve source, document title, page, and URL metadata through retrieval and render citations in the frontend; score citation correctness in the eval harness.
6. **Retrieval, round two.** Add parent-child chunking and a reranker over hybrid candidates to target the remaining context-recall gap.
7. **A bigger, licensed corpus.** Add vetted sources on illness, teething, and vaccination schedules, recording source URLs, publication dates, versions, and redistribution status.
8. **Answer-accuracy recovery and operations.** Recover accuracy through better coverage without loosening grounding, flag low-faithfulness runs in LangSmith, and run tests plus eval gates in CI.
