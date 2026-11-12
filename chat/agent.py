# EECE430 Assignment 3 - Omar Tabsh (202400798)
import json
import os

from google import genai

from .tools import TOOL_DECLARATIONS, TOOL_FUNCTIONS

MODEL = "gemini-3.8-flash"

SYSTEM_PROMPT = """You are an inventory assistant for a small warehouse.

You help the user check and update stock and prices by calling the tools available to you.

Rules:
- Always use a tool to answer questions about stock or prices. Never guess or rely on memory.
- For the cost of buying items (including any VAT or tax percentage), use the calculate_cost tool instead of doing the arithmetic yourself, and show the subtotal, VAT amount and total.
- Prices are in US dollars.
- Reply in plain text only. Do not use Markdown formatting such as ** or bullet symbols.
- If a tool returns an error, explain the problem to the user in plain language.
- Before deleting an item entirely, make sure that is what the user meant.
- Keep your answers short and factual.
- Do not answer any question unrelated to the inventory task.
"""

MAX_STEPS = 5

_client = None


def get_client():
    """Create the Gemini client on first use, so the app (and CI checks) can
    start even when GEMINI_API_KEY is not set."""
    global _client
    if _client is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not set.")
        _client = genai.Client(api_key=api_key)
    return _client


def run_agent(user_message, previous_interaction_id=None, verbose=False):
    """Send a message to the agent and run tools until it produces an answer."""

    client = get_client()

    interaction = client.interactions.create(
        model=MODEL,
        input=user_message,
        tools=TOOL_DECLARATIONS,
        system_instruction=SYSTEM_PROMPT,
        previous_interaction_id=previous_interaction_id,
    )

    for _ in range(MAX_STEPS):
        calls = [s for s in interaction.steps if s.type == "function_call"]

        if not calls:
            return interaction.output_text, interaction.id

        results = []
        for call in calls:
            function = TOOL_FUNCTIONS[call.name]
            output = function(**call.arguments)

            if verbose:
                print(f"  -> {call.name}({call.arguments}) = {output}")

            results.append({
                "type": "function_result",
                "name": call.name,
                "call_id": call.id,
                "result": [{"type": "text", "text": json.dumps(output)}],
            })

        interaction = client.interactions.create(
            model=MODEL,
            input=results,
            tools=TOOL_DECLARATIONS,
            system_instruction=SYSTEM_PROMPT,
            previous_interaction_id=interaction.id,
        )

    return "I got stuck working on that. Please try rephrasing.", interaction.id