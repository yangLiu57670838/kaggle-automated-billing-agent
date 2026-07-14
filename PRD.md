# Product Requirements Document (PRD)
## Kaggle Automated Billing Agent

**Version:** 1.0  
**Date:** 2026-07-07  
**Author:** You  
**Status:** Draft  
**Tracking:** [TODO.md](TODO.md) — active implementation tasks linked to this PRD

---

## 1. Executive Summary

Build an **Agentic AI pipeline** that reads natural-language purchase-order emails, extracts order details, and computes invoice totals using **three deterministic Python tools** — never letting the LLM do arithmetic directly. The agent follows the **ReAct (Reason + Act)** pattern: the model reasons about the email, calls tools in sequence, and outputs a `Total_Bill` for each row in `test.csv`.

**Success metric:** Lowest **RMSE** between predicted `Total_Bill` and ground-truth math on the Kaggle leaderboard.

---

## 2. Problem Statement

| Pain Point | Impact |
|---|---|
| Thousands of PO emails arrive daily in free text | Manual invoice creation is slow and error-prone |
| LLMs read text well but hallucinate math | Wrong totals on financial documents |
| Competition requires precision | RMSE punishes any calculation mistake |

**Core insight:** Separate **language understanding** (LLM) from **numeric computation** (Python tools).

---

## 3. Goals & Non-Goals

### Goals
- [ ] Parse `email_text` to extract: `quantity`, `unit_price`, `discount_percent`, `shipping_fee`
- [ ] Implement three tools with exact arithmetic
- [ ] Build a ReAct agent that **must** call tools in order
- [ ] Process all rows in `test.csv` and produce `submission.csv`
- [ ] Achieve RMSE as close to 0 as possible

### Non-Goals
- Building a production email server or UI
- Training/fine-tuning a custom model (use an off-the-shelf LLM API or local model)
- Handling ambiguous or malformed emails beyond what the dataset contains

---

## 4. System Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────────────┐
│  test.csv   │────▶│  Inference       │────▶│  submission.csv         │
│  email_text │     │  Pipeline        │     │  order_id, Total_Bill   │
└─────────────┘     └────────┬─────────┘     └─────────────────────────┘
                             │
                    ┌────────▼─────────┐
                    │  ReAct Agent     │
                    │  (LLM + loop)    │
                    └────────┬─────────┘
                             │ tool calls
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
     calculate_subtotal  apply_discount  calculate_final_total
              │              │              │
              └──────────────┴──────────────┘
                    Pure Python math
```

### Data Flow (per order)

1. **Input:** `email_text` string
2. **Agent thinks:** Identify quantity, unit price, discount %, shipping fee
3. **Tool 1:** `calculate_subtotal(quantity, unit_price)` → `subtotal`
4. **Tool 2:** `apply_discount(subtotal, discount_percent)` → `discounted_amount`
5. **Tool 3:** `calculate_final_total(discounted_amount, shipping_fee)` → `Total_Bill`
6. **Output:** `Total_Bill` as a float

### Example Walkthrough

**Email:** *"Hello, we would like to order 50 office chairs. The agreed price is 120 dollars per chair. We are eligible for the 15 percent bulk discount. Please include the 250 dollar delivery fee."*

| Step | Action | Result |
|------|--------|--------|
| Extract | quantity=50, unit_price=120, discount=15, shipping=250 | — |
| Tool 1 | `calculate_subtotal(50, 120)` | 6000.0 |
| Tool 2 | `apply_discount(6000, 15)` | 5100.0 |
| Tool 3 | `calculate_final_total(5100, 250)` | **5350.0** |

---

## 5. Tool Specifications

All tools live in `src/tools/`. They must use **float arithmetic** and return **float** values.

### 5.1 `calculate_subtotal(quantity: int, unit_price: float) -> float`

```
subtotal = quantity × unit_price
```

### 5.2 `apply_discount(subtotal: float, discount_percent: float) -> float`

```
discounted_amount = subtotal × (1 - discount_percent / 100)
```

> If discount is 0%, return subtotal unchanged.

### 5.3 `calculate_final_total(discounted_amount: float, shipping_fee: float) -> float`

```
total_bill = discounted_amount + shipping_fee
```

### Tool Binding Rules
- Tools are registered with the agent framework (LangChain, LlamaIndex, or custom ReAct loop)
- The LLM receives tool **names, descriptions, and JSON schemas** — not the implementation
- Agent prompt must instruct: **"Never calculate math yourself; always use the provided tools."**

---

## 6. Agent Design (ReAct)

### 6.1 ReAct Loop

```
THOUGHT → ACTION (tool call) → OBSERVATION → THOUGHT → ... → FINAL ANSWER
```

| Phase | Responsibility |
|-------|----------------|
| **Thought** | LLM parses email, decides which tool to call next |
| **Action** | Execute one Python tool with extracted arguments |
| **Observation** | Tool return value fed back to LLM |
| **Final Answer** | `Total_Bill` after all three tools have run |

### 6.2 Prompt Strategy (`src/agent/prompts.py`)

The system prompt should include:
1. Role: invoice automation agent
2. Available tools with signatures and when to use each
3. Strict rule: extract entities from email, call tools in order
4. Output format: final `Total_Bill` as a number
5. Few-shot example (optional, using the training example from the competition overview)

### 6.3 Entity Extraction Hints

Emails vary in phrasing. The agent must handle patterns like:

| Field | Example Phrasings |
|-------|-------------------|
| quantity | "order 50 office chairs", "Need 61 standing desks", "137 monitors" |
| unit_price | "$120 each", "agreed price is 1720.4 dollars per unit", "Unit cost is 2321.36" |
| discount | "15 percent bulk discount", "standard 5% discount", "Discount rate is 17%" |
| shipping | "250 dollar delivery fee", "add $400 for expedited shipping", "Freight is a flat 126.94" |

---

## 7. File & Module Map

```
kaggle-automated-billing-agent/
├── PRD.md                          ← This document
├── TODO.md                         ← Active tasks; linked to PRD phases & risks
├── README.md                       ← Setup, run instructions, competition link
├── requirements.txt                ← Python dependencies
├── .env.example                    ← API keys template (OPENAI_API_KEY, etc.)
├── .gitignore
├── test.csv                        ← Kaggle test data (provided)
│
├── data/
│   └── sample_train.csv            ← Local dev examples with expected_bill
│
├── configs/
│   └── config.yaml                 ← Model name, temperature, paths
│
├── src/
│   ├── __init__.py
│   ├── tools/
│   │   ├── __init__.py             ← Export all three tools
│   │   ├── calculate_subtotal.py
│   │   ├── apply_discount.py
│   │   └── calculate_final_total.py
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── react_agent.py          ← ReAct loop + tool binding
│   │   └── prompts.py              ← System & few-shot prompts
│   └── pipeline/
│       ├── __init__.py
│       └── inference.py            ← Batch process test.csv → submission.csv
│
├── scripts/
│   ├── run_local_test.py           ← Run agent on sample_train.csv
│   ├── generate_submission.py      ← CLI entry point for Kaggle submit
│   └── evaluate_rmse.py          ← Local RMSE if you have labels
│
├── tests/
│   ├── __init__.py
│   ├── test_tools.py               ← Unit tests for the three tools
│   ├── test_agent.py               ← Integration test with known email
│   └── fixtures/
│       └── sample_orders.json      ← Test cases with expected totals
│
├── notebooks/
│   ├── 01_explore_and_prototype.ipynb      ← EDA, prompt tuning, debugging
│   └── 02_kaggle_submission_record.ipynb   ← Single notebook for Kaggle record after final result
│
└── outputs/
    └── .gitkeep                    ← submission.csv written here
```

---

## 8. Implementation Phases (Step-by-Step)

### Phase 0 — Environment Setup
- [ ] Create virtual environment: `python -m venv .venv`
- [ ] Install dependencies from `requirements.txt`
- [ ] Copy `.env.example` → `.env` and add API key
- [ ] Verify `test.csv` loads correctly

### Phase 1 — Tools (Day 1)
**Files:** `src/tools/*.py`, `tests/test_tools.py`

- [ ] Implement `calculate_subtotal`
- [ ] Implement `apply_discount`
- [ ] Implement `calculate_final_total`
- [ ] Write unit tests with known inputs/outputs
- [ ] Run: `pytest tests/test_tools.py`

**Exit criteria:** All tool tests pass; competition example returns `5350.0`.

### Phase 2 — Prompts & Agent Skeleton (Day 1–2)
**Files:** `src/agent/prompts.py`, `src/agent/react_agent.py`

- [ ] Write system prompt with tool descriptions
- [ ] Choose agent framework (recommend: **LangChain** `create_react_agent` or a minimal custom loop)
- [ ] Bind the three tools to the LLM
- [ ] Test on the single training example from the competition overview
- [ ] Inspect agent trace: confirm all 3 tools are called in order

**Exit criteria:** Agent returns `5350.0` for the overview example without hallucinating math.

### Phase 3 — Local Evaluation (Day 2)
**Files:** `data/sample_train.csv`, `scripts/run_local_test.py`, `scripts/evaluate_rmse.py`

- [ ] Create `sample_train.csv` with 5–10 labeled rows (mix of phrasing styles from `test.csv`)
- [ ] Run batch inference locally
- [ ] Compute RMSE on sample set
- [ ] Debug failures: extraction errors vs. tool errors

**Exit criteria:** RMSE = 0 on sample_train.csv.

### Phase 4 — Full Inference & Submission (Day 2–3)
**Files:** `src/pipeline/inference.py`, `scripts/generate_submission.py`

- [ ] Process all rows in `test.csv`
- [ ] Output `outputs/submission.csv` with columns: `order_id`, `Total_Bill`
- [ ] Validate: no NaN, correct row count, float precision
- [ ] Submit to Kaggle

**Exit criteria:** Valid submission file uploaded; leaderboard score received.

### Phase 5 — Iterate & Improve (Ongoing)
- [ ] Review wrong predictions (if public leaderboard feedback available)
- [ ] Tune prompts for edge phrasings ("0% discount", "flat freight", etc.)
- [ ] Add retry logic for malformed agent outputs
- [ ] Consider fallback regex extractor if LLM misses a field

### Phase 6 — Kaggle Notebook Record (After Final Result)
**Files:** `notebooks/02_kaggle_submission_record.ipynb`

After you have a final `submission.csv` and leaderboard score, create **one** Kaggle notebook as the competition / portfolio record (not for day-to-day development).

- [ ] Create a single notebook that documents the end-to-end solution
- [ ] Include: problem summary, ReAct agent + three tools, how `Total_Bill` is computed, how `submission.csv` is produced
- [ ] Prefer importing / calling project code (`src/`) rather than re-implementing logic in the notebook
- [ ] Optionally re-run inference and write `submission.csv` from the notebook for reproducibility
- [ ] Publish / upload the notebook on Kaggle as the official run record

**Exit criteria:** One public (or competition-attached) Kaggle notebook that reproduces the final submission approach.

---

## 9. Submission Format

| Column | Type | Description |
|--------|------|-------------|
| `order_id` | int | From `test.csv` |
| `Total_Bill` | float | Agent-computed final invoice total |

**File:** `submission.csv`  
**Example row:** `19,235432.87`

---

## 10. Technical Decisions (To Fill In)

| Decision | Options | Your Choice |
|----------|---------|-------------|
| LLM provider | OpenAI, Anthropic, Ollama (local), Groq | _TBD_ |
| Agent framework | LangChain, LlamaIndex, custom ReAct | _TBD_ |
| Model size | gpt-4o-mini, llama3:8b, etc. | _TBD_ |
| Temperature | 0 (recommended for determinism) | _TBD_ |

**Recommendation for beginners:** LangChain + OpenAI `gpt-4o-mini` at `temperature=0`. Simple API, good tool-calling support, low cost.

---

## 11. Risks & Mitigations

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| LLM skips a tool and guesses the total | High | Strong prompt + validate that 3 tool calls occurred |
| Wrong entity extraction (e.g., confuses discount with shipping) | Medium | Few-shot examples covering varied phrasings |
| Float precision / rounding mismatch | Low | Match competition math exactly; avoid rounding mid-pipeline |
| API rate limits on full test set | Medium | Batch with retries; cache results per order_id |
| Agent infinite loop | Low | Set `max_iterations` (e.g., 10) |

---

## 12. Testing Checklist

### Unit Tests (`tests/test_tools.py`)
- [ ] `calculate_subtotal(50, 120)` == 6000.0
- [ ] `apply_discount(6000, 15)` == 5100.0
- [ ] `apply_discount(1000, 0)` == 1000.0
- [ ] `calculate_final_total(5100, 250)` == 5350.0
- [ ] Full pipeline on competition example == 5350.0

### Integration Tests (`tests/test_agent.py`)
- [ ] Agent calls exactly 3 tools per email
- [ ] Agent handles "0% discount" emails
- [ ] Agent handles "$" and "dollars" and "per unit" variants

### Submission Validation
- [ ] Row count matches `test.csv`
- [ ] All `order_id` values present
- [ ] No missing `Total_Bill` values
- [ ] All values are positive floats

---

## 13. Learning Resources (First-Time Agent Builders)

1. **ReAct paper:** [Synergizing Reasoning and Acting in Language Models](https://arxiv.org/abs/2210.03629)
2. **LangChain ReAct agent:** [docs](https://python.langchain.com/docs/concepts/agents/)
3. **Tool calling concept:** LLM outputs structured JSON → your code runs Python → result goes back to LLM
4. **Key mental model:** LLM = planner/reader; Python tools = calculator

---

## 14. Open Questions

- [ ] Does Kaggle provide a `sample_submission.csv` format file?
- [ ] Is there a public training set with `expected_bill`, or only the one example?
- [ ] What float precision does the grader expect (2 decimals? full precision)?
- [ ] Are there hidden test cases with trickier phrasing?

---

## 15. Definition of Done

See [TODO.md](TODO.md) for in-progress work items.

- [ ] Three tools implemented and unit-tested
- [ ] ReAct agent processes an email end-to-end using only tools for math
- [ ] `submission.csv` generated for full `test.csv`
- [ ] Submitted to Kaggle with a competitive RMSE
- [ ] README documents how to reproduce locally
- [ ] Single Kaggle notebook created/published as a record after the final result (Phase 6)
