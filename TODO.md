# TODO

Linked to [PRD.md](PRD.md) — tasks below map to agent design (§6), risks (§11), and Definition of Done (§15).

- [ ] **Refine agent system prompt** (`src/agent/prompts.py`) — [PRD §6.2 Prompt Strategy](PRD.md#62-prompt-strategy-srcagentpromptspy), [PRD §11 LLM hallucination risk](PRD.md#11-risks--mitigations) — strengthen rules so the model never computes totals itself, always calls all three tools in order, and only returns the `Total_Bill` from the last tool result (not a guessed number). Add explicit anti-hallucination constraints: no skipping tools, no intermediate math in the final reply, restate extracted fields before tool calls, and handle edge cases (`0%` discount, varied currency phrasing).
