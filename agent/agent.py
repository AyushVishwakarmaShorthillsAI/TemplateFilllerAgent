from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.tools.tool_context import ToolContext

from .subagents.pruner.agent import pruner_agent
from .subagents.filler.agent import filler_agent
from .subagents.enricher.agent import enricher_agent

from .instructions import INSTRUCTIONS


# =========================
# ROOT TOOLS
# =========================

def save_initial_inputs(
    initial_template: str,
    reviewed_summary: str,
    tool_context: ToolContext,
):
    """Store the user-provided template and reviewed clinical summary into shared state.

    Call this tool exactly once at the start, immediately after the user provides
    both inputs. Do not modify or analyze the content; only persist it for the
    pipeline (pruner, filler, enricher) to use.

    Args:
        initial_template: The raw template text from the user. Exact text to be
            pruned and filled later. Do not alter.
        reviewed_summary: The reviewed clinical summary from the user. Source
            of truth for filling and enriching the template. Do not alter.
        tool_context: ADK tool context (injected); provides access to shared state.
    """
    tool_context.state["template"] = initial_template
    tool_context.state["reviewed_summary"] = reviewed_summary

    return {
        "status": "success",
        "state_updated": ["template", "reviewed_summary"]
    }


def save_final_filled_template(
    final_filled_template: str,
    tool_context: ToolContext,
):
    """Store the completed document and mark the workflow as finalized.

    Call this tool exactly once after the template_processing_pipeline has
    completed. Pass the value that was written to state['enriched_template']
    by the enricher sub-agent. This becomes the official final output.

    Args:
        final_filled_template: The completed document text (same as
            state['enriched_template'] after the pipeline runs). Must be the
            full enriched template, not a summary or excerpt.
        tool_context: ADK tool context (injected); provides access to shared state.
    """
    tool_context.state["final_filled_template"] = final_filled_template

    return {
        "status": "success",
        "state_updated": ["final_filled_template"],
    }


def display_all_states(tool_context: ToolContext):
    """Return a structured list of all pipeline state keys and their values for the user to see.

    Call this when the user asks to display or show all saved states. Reads from shared state:
    template, reviewed_summary, then each template followed by its reasoning (pruned_template,
    pruned_template_reasoning, filled_template, filled_template_reasoning, enriched_template,
    enriched_template_reasoning), then final_filled_template. Return this tool's output to
    the user verbatim when they ask to see saved state.

    Args:
        tool_context: ADK tool context (injected); provides access to shared state.
    """
    keys = [
        "template",
        "reviewed_summary",
        "pruned_template",
        "pruned_template_reasoning",
        "filled_template",
        "filled_template_reasoning",
        "enriched_template",
        "enriched_template_reasoning",
        "final_filled_template",
    ]
    lines = [
        "--- BEGIN PIPELINE STATE ---",
        "",
    ]
    for i, key in enumerate(keys, 1):
        value = tool_context.state.get(key, "")
        if not value:
            display_value = "(empty)"
        elif isinstance(value, str) and len(value) > 300:
            display_value = value + "\n"
        else:
            display_value = value
        lines.append(f"{i}. {key}:")
        lines.append(f"   {display_value}")
        lines.append("")
    lines.append("--- END PIPELINE STATE ---")
    return "\n".join(lines)


# =========================
# SEQUENTIAL WORKFLOW
# =========================

pipeline_agent = SequentialAgent(
    name='template_processing_pipeline',
    sub_agents=[
        pruner_agent,
        filler_agent,
        enricher_agent,
    ],
)


# =========================
# ROOT AGENT
# =========================

root_agent = LlmAgent(
    name="template_filler",
    model="gemini-2.5-pro",
    description="Root agent handling user IO and executing template processing workflow.",
    sub_agents=[pipeline_agent],
    tools=[save_initial_inputs, save_final_filled_template, display_all_states],
    instruction=INSTRUCTIONS,
    output_key="all_states"
)
