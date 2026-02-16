# Loop Agent Strategy & Root Agent Instructions

This document describes how the template-filling pipeline is converted to a **LoopAgent** (max 5 iterations), the desired output, and the improved role of the **orchestrator (root agent)**. It is based on the [ADK Loop agents documentation](https://google.github.io/adk-docs/agents/workflow-agents/loop-agents/).

---

## 1. How ADK Loop Agents Work

- **LoopAgent** runs its sub-agents **repeatedly** in order (a loop), for a fixed number of iterations or until a termination condition is met.
- It is **not** LLM-powered; execution order is deterministic. The **sub-agents** (e.g. LlmAgents) do the reasoning.
- **Termination** (required to avoid infinite loops):
  - **Max iterations**: The loop stops after `max_iterations` (e.g. 5).
  - **Escalation**: A sub-agent can signal “stop” by setting `tool_context.actions.escalate = True`, typically via the **exit_loop** tool. When any event has `escalate = True`, the loop exits immediately after that sub-agent finishes.

So we **must** either set `max_iterations` or have a sub-agent call **exit_loop** (or both).

---

## 2. Current vs New Pipeline

| Aspect | Current (Sequential) | New (Loop) |
|--------|---------------------|------------|
| Agent type | `SequentialAgent` | `LoopAgent` |
| Run | Pruner → Filler → Enricher **once** | Same sequence **up to 5 times** |
| Stop condition | After one full pass | After **exit_loop** (quality OK) or **5 iterations** |
| Refinement | None | Optional: evaluator gives feedback; next iteration can use it |

---

## 3. Strategy: What the Loop Runs

### 3.1 Sub-agents inside the loop (in order)

1. **Pruner** – Prunes `template` using `reviewed_summary` → writes `pruned_template`.
2. **Filler** – Fills `pruned_template` using `reviewed_summary` → writes `filled_template`.
3. **Enricher** – Enriches `filled_template` using `reviewed_summary` → writes `enriched_template`.
4. **Evaluator** (new) – Reads `enriched_template` (and optionally `reviewed_summary`).  
   - If quality is satisfactory → calls **exit_loop** → loop ends.  
   - If not → does **not** call exit_loop; can write **refinement_feedback** to state for the next iteration.

### 3.2 State used across iterations

- **Fixed per run**: `template`, `reviewed_summary` (set once by the root).
- **Overwritten each iteration**: `pruned_template`, `filled_template`, `enriched_template`.
- **Optional**: `refinement_feedback` – written by the evaluator when it does not exit; Pruner/Filler/Enricher instructions can say “if refinement_feedback is present, apply it when pruning/filling/enriching.”

So each iteration is: same `template` + `reviewed_summary`, possibly with `refinement_feedback` from the previous run. The last iteration’s `enriched_template` is the **desired output** of the loop.

### 3.3 Desired output of the loop

- **Success (early exit)**: When the evaluator calls **exit_loop**, the loop stops and `state['enriched_template']` is the final document.
- **Success (max iterations)**: After 5 full cycles, the loop stops and `state['enriched_template']` is the final document (best effort after 5 refinements).

In both cases the **orchestrator** treats `state['enriched_template']` as the completed document and saves/returns it.

---

## 4. Role of the Orchestrator (Root Agent)

The **root agent** is the orchestrator. It:

1. **Input**: Receives template + reviewed clinical summary from the user.
2. **Persist**: Saves them to state via **save_initial_inputs** (no editing).
3. **Run loop**: Delegates to the **template_processing_pipeline** (LoopAgent). It does **not** reorder or repeat steps; it invokes the pipeline once.
4. **After the loop**: Reads `state['enriched_template']`, treats it as the final document.
5. **Finalize**: Calls **save_final_filled_template** with that value.
6. **Verification**: Optionally calls **display_all_states** for debugging.
7. **Response**: Returns the final filled template to the user (or, if the user asked to “display all states”, returns the exact output of **display_all_states**).

The orchestrator **refines** only in the sense of **oversight**: it does not edit text; it ensures the loop runs, then **reviews** the final `enriched_template` and delivers it as the single authoritative output.

---

## 5. Improved Root Agent Instructions (for Loop Pipeline)

Below are the **new instructions** for the root agent so it behaves as the orchestrator for the loop-based pipeline.

```text
Persona:
You are the root orchestrator of a medical document generation pipeline that uses an iterative (loop) workflow.
You handle user inputs, initialize shared state, run the loop pipeline once, and then finalize and return the result.
You DO NOT edit template content yourself. All document processing is done by sub-agents inside the loop.

=====================
INPUT HANDLING
=====================
The user provides:
1. A template
2. A reviewed clinical summary

Store them in shared state immediately using the tool save_initial_inputs:

{
  "initial_template": "<user template>",
  "reviewed_summary": "<user reviewed summary>"
}

Do not modify or analyze the content yourself.

=====================
WORKFLOW EXECUTION (LOOP PIPELINE)
=====================
After saving the inputs, delegate to the workflow sub-agent: template_processing_pipeline.

The pipeline is a LOOP that runs up to 5 iterations. In each iteration it runs, in order:
- pruner   → pruned_template
- filler   → filled_template
- enricher → enriched_template
- evaluator → may call exit_loop (quality OK) or leave feedback for the next iteration

The loop stops when:
- The evaluator calls exit_loop (quality satisfactory), or
- 5 iterations have been completed.

You must NOT run the pipeline multiple times yourself. Invoke it once; it will loop internally.

=====================
AFTER THE LOOP COMPLETES
=====================
Read the final value from state['enriched_template']. This is the completed document.

Call save_final_filled_template with that value:

{
  "final_filled_template": "<value of state['enriched_template']>"
}

=====================
STATE VERIFICATION
=====================
After saving final_filled_template, call display_all_states once (no arguments) for verification.

=====================
WHEN USER ASKS TO "DISPLAY ALL STATES" OR "SHOW SAVED STATE"
=====================
If the user asks to display, show, or list (all) saved state(s):
1. Call the tool display_all_states (no arguments).
2. Return the EXACT output of that tool as your response. Do not summarize or replace with the filled template.

=====================
NORMAL OUTPUT (when user asked for filled document)
=====================
When the user did NOT ask to display state, after calling display_all_states, return the final filled template content as the response. Do not add explanations.

=====================
CRITICAL RULES
=====================
- Never edit template content yourself.
- Invoke the pipeline exactly once; the pipeline manages the loop (up to 5 iterations) and exit_loop.
- Sub-agents perform all transformations; you only save inputs, run the pipeline, then save and return the final output.
- When the user explicitly asks to "display all states" / "show saved state", your reply MUST be the exact output of display_all_states, nothing else.

=====================
CLARIFICATION
=====================
Ask the user for clarification only if the template or reviewed clinical summary is missing.
```

---

## 6. Implementation Checklist

- [ ] Add **Evaluator** sub-agent (LlmAgent) with:
  - Instruction: review `enriched_template` (and optionally `reviewed_summary`); if quality is good, call **exit_loop**; else optionally set **refinement_feedback** in state.
  - Tool: **exit_loop** (from `google.adk.tools.exit_loop`).
  - Output or state: optionally `refinement_feedback`.
- [ ] Replace **SequentialAgent** with **LoopAgent** for `template_processing_pipeline`:
  - `sub_agents=[pruner_agent, filler_agent, enricher_agent, evaluator_agent]`
  - `max_iterations=5`
- [ ] (Optional) Add **refinement_feedback** to state and update Pruner/Filler/Enricher instructions: “If state has refinement_feedback, apply it when producing the next pruned/filled/enriched template.”
- [ ] Update root agent **instructions** to the improved version above (loop pipeline, single invocation, post-loop finalization).

---

## 7. Summary

- **Loop agent**: Runs Pruner → Filler → Enricher → Evaluator in a loop (max 5). Evaluator exits via **exit_loop** when satisfied.
- **Desired output**: `state['enriched_template']` when the loop exits (either by exit_loop or by hitting 5 iterations).
- **Orchestrator**: Saves inputs, runs the loop pipeline once, then saves and returns the final `enriched_template`; does not edit content and does not run the pipeline multiple times.

This keeps the orchestrator simple and aligns with the [ADK Loop agents](https://google.github.io/adk-docs/agents/workflow-agents/loop-agents/) design: deterministic loop with a clear exit condition and a single final document.
