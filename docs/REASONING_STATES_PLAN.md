# Plan: Add Reasoning States for Pruner, Filler, Enricher

## Goal
Each sub-agent (pruner, filler, enricher) produces **reasoning** explaining why each line/section in its output appears, compared to **reviewed_summary** and the **initial template**. This reasoning is saved to state and displayed in `display_all_states` immediately after the corresponding template.

---

## 1. New State Keys

| State key | Set by | Content |
|-----------|--------|--------|
| `pruned_template_reasoning` | Pruner | Why each line/section was KEPT or REMOVED vs template + reviewed_summary |
| `filled_template_reasoning` | Filler | Why each filled value was chosen (support from reviewed_summary / template) |
| `enriched_template_reasoning` | Enricher | Why each added line/section was included and where (source in reviewed_summary) |

---

## 2. Where Changes Are Made

### 2.1 Pruner sub-agent

| File | Change |
|------|--------|
| **`agent/subagents/pruner/agent.py`** | Add tool `save_pruned_template_reasoning(pruned_template_reasoning: str)`. Register it on `pruner_agent` with `save_pruned_template`. |
| **`agent/subagents/pruner/instructions.py`** | Add instruction: after producing the pruned template, produce reasoning (per line/section: KEEP/REMOVE and why, referencing template and reviewed_summary). Call `save_pruned_template` first, then `save_pruned_template_reasoning` exactly once. |

### 2.2 Filler sub-agent

| File | Change |
|------|--------|
| **`agent/subagents/filler/agent.py`** | Add tool `save_filled_template_reasoning(filled_template_reasoning: str)`. Register it on `filler_agent` with `save_filled_template`. |
| **`agent/subagents/filler/instructions.py`** | Add instruction: after producing the filled template, produce reasoning (per filled value or section: which part of reviewed_summary or template supports it). Call `save_filled_template` first, then `save_filled_template_reasoning` exactly once. |

### 2.3 Enricher sub-agent

| File | Change |
|------|--------|
| **`agent/subagents/enricher/agent.py`** | Add tool `save_enriched_template_reasoning(enriched_template_reasoning: str)`. Register it on `enricher_agent` with `save_enriched_template`. |
| **`agent/subagents/enricher/instructions.py`** | Add instruction: after producing the enriched template, produce reasoning (per added line/section: which fact from reviewed_summary, where inserted). Call `save_enriched_template` first, then `save_enriched_template_reasoning` exactly once. |

### 2.4 Root agent

| File | Change |
|------|--------|
| **`agent/agent.py`** | In `display_all_states`, change the list of keys so each template is followed by its reasoning: `template`, `reviewed_summary`, `pruned_template`, `pruned_template_reasoning`, `filled_template`, `filled_template_reasoning`, `enriched_template`, `enriched_template_reasoning`, `final_filled_template`. |

---

## 3. Order of Tool Calls (per sub-agent)

- **Pruner**: Call `save_pruned_template` → then `save_pruned_template_reasoning`.
- **Filler**: Call `save_filled_template` → then `save_filled_template_reasoning`.
- **Enricher**: Call `save_enriched_template` → then `save_enriched_template_reasoning`.

---

## 4. Display order in `display_all_states`

1. template  
2. reviewed_summary  
3. pruned_template  
4. **pruned_template_reasoning**  
5. filled_template  
6. **filled_template_reasoning**  
7. enriched_template  
8. **enriched_template_reasoning**  
9. final_filled_template  

Reasoning is always shown immediately after its corresponding template.
