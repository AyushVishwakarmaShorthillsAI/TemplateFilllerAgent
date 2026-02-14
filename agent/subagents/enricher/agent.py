from google.adk.agents import LlmAgent
from .instructions import INSTRUCTIONS
from google.adk.tools.tool_context import ToolContext


def save_enriched_template(enriched_template: str, tool_context: ToolContext):
    """Save the enriched template to shared state. Call exactly once with the final enriched text.

    After enriching the filled template by adding relevant facts from reviewed_summary
    that were not already in the template (additive only; no removal or rephrasing),
    call this tool with the complete enriched template. Do not return as normal text;
    the tool call is the only valid final action.

    Args:
        enriched_template: The full enriched template text. Filled content plus
            additional relevant facts from the summary, inserted at appropriate
            places. Existing text unchanged; no repetition of already-stated facts.
        tool_context: ADK tool context (injected); provides access to shared state.
    """
    tool_context.state["enriched_template"] = enriched_template

    return {
        "status": "success",
        "state_updated": ["enriched_template"],
        "message": "Enriched template saved successfully.",
    }


enricher_agent = LlmAgent(
    name="enricher",
    model="gemini-2.5-flash",
    description="Subagent that enriches the filled template with additional relevant clinical information.",
    instruction=INSTRUCTIONS,
    tools=[save_enriched_template],
)
