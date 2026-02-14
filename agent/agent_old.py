from google.adk.agents import LlmAgent
from .instructions import INSTRUCTIONS

from .subagents.enricher.agent import enricher_agent
from .subagents.filler.agent import filler_agent
from .subagents.pruner.agent import pruner_agent

from google.adk.tools.tool_context import ToolContext


def save_initial_inputs(initial_template: str,
                        reviewed_summary: str,
                        tool_context: ToolContext):

    tool_context.state["template"] = initial_template
    tool_context.state["reviewed_summary"] = reviewed_summary

    return {
        "status": "success",
        "state_updated": ["template", "reviewed_summary"],
        "message": "Initial inputs saved successfully."
    }


def save_final_filled_template(final_filled_template: str,
                               tool_context: ToolContext):

    tool_context.state["final_filled_template"] = final_filled_template

    return {
        "status": "success",
        "state_updated": "final_filled_template",
        "message": "Final filled template saved successfully."
    }


root_agent = LlmAgent(
    name="template_filler",
    model="gemini-2.5-pro",
    description="Orchestrator agent coordinating pruner, filler, and enricher subagents to produce a finalized filled template.",
    sub_agents=[pruner_agent, filler_agent, enricher_agent],
    tools=[save_initial_inputs, save_final_filled_template],
    instruction=INSTRUCTIONS
)
