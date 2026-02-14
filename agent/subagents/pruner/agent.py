from google.adk.agents import LlmAgent
from .instructions import INSTRUCTIONS
from google.adk.tools.tool_context import ToolContext


def save_pruned_template(pruned_template: str, tool_context: ToolContext):
    """Save the pruned template to shared state. Call exactly once with the final pruned text.

    After pruning the template (keeping only sections supported by reviewed_summary,
    removing unsupported content, preserving placeholders and formatting), call this
    tool with the complete pruned template. Do not return the template as normal
    text; the tool call is the only valid final action.

    Args:
        pruned_template: The full pruned template text. Only KEEP or REMOVE was
            applied; no editing, filling, or rephrasing. Placeholders like
            {name of condition} unchanged. Formatting and structure preserved.
        tool_context: ADK tool context (injected); provides access to shared state.
    """
    tool_context.state["pruned_template"] = pruned_template

    return {
        "status": "success",
        "state_updated": ["pruned_template"],
        "message": "Pruned template saved successfully.",
    }


pruner_agent = LlmAgent(
    name="pruner",
    model="gemini-2.5-flash",
    description="Subagent that prunes unsupported content from the template.",
    instruction=INSTRUCTIONS,
    tools=[save_pruned_template]
)
