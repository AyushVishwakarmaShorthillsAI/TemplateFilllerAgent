from google.adk.agents import LlmAgent
from .instructions import INSTRUCTIONS
from google.adk.tools.tool_context import ToolContext


def save_filled_template(filled_template: str, tool_context: ToolContext):
    """Save the filled template to shared state. Call exactly once with the final filled text.

    After filling the pruned template using only facts from reviewed_summary (replacing
    placeholders, adding complete statistics, plain language), call this tool with
    the complete filled template. Do not return the template as normal text; the
    tool call is the only valid final action.

    Args:
        filled_template: The full filled template text. All placeholders replaced
            with data from reviewed_summary. No new information added; template
            wording and structure preserved.
        tool_context: ADK tool context (injected); provides access to shared state.
    """
    tool_context.state["filled_template"] = filled_template

    return {
        "status": "success",
        "state_updated": ["filled_template"],
        "message": "Filled template saved successfully.",
    }


def save_filled_template_reasoning(filled_template_reasoning: str, tool_context: ToolContext):
    """Save the reasoning for the filled template to shared state. Call once after save_filled_template.

    Explain why each filled value or section was chosen, referencing reviewed_summary and
    the pruned template.

    Args:
        filled_template_reasoning: Explanation per filled value/section: which part of
            reviewed_summary or template supports it.
        tool_context: ADK tool context (injected); provides access to shared state.
    """
    tool_context.state["filled_template_reasoning"] = filled_template_reasoning
    return {
        "status": "success",
        "state_updated": ["filled_template_reasoning"],
        "message": "Filled template reasoning saved successfully.",
    }


filler_agent = LlmAgent(
    name="filler",
    model="gemini-2.5-pro",
    description="Subagent that fills the pruned template using reviewed clinical summary.",
    instruction=INSTRUCTIONS,
    tools=[save_filled_template, save_filled_template_reasoning],
)
