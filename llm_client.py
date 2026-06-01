"""
Model-agnostic LLM client.

Switch providers by setting LLM_PROVIDER in your environment or
.streamlit/secrets.toml:
  LLM_PROVIDER = "anthropic"   # default
  LLM_PROVIDER = "gemini"      # for UC Berkeley / Google Workspace
"""

import os


def provider_label() -> str:
    """Human-readable string showing active provider and model."""
    provider = os.environ.get("LLM_PROVIDER", "anthropic").lower()
    if provider == "gemini":
        model = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
        return f"Gemini ({model})"
    model = os.environ.get("ANTHROPIC_MODEL", "claude-opus-4-8")
    return f"Claude ({model})"


def call_llm(
    system: str,
    user: str,
    use_search: bool = False,
    max_tokens: int = 8192,
) -> str:
    """Call the configured LLM provider and return the response text."""
    provider = os.environ.get("LLM_PROVIDER", "anthropic").lower()
    if provider == "gemini":
        return _call_gemini(system, user, use_search, max_tokens)
    return _call_anthropic(system, user, use_search, max_tokens)


# ---------------------------------------------------------------------------
# Anthropic
# ---------------------------------------------------------------------------

def _call_anthropic(system: str, user: str, use_search: bool, max_tokens: int) -> str:
    import anthropic
    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env
    model = os.environ.get("ANTHROPIC_MODEL", "claude-opus-4-8")
    tools = (
        [{"type": "web_search_20250305", "name": "web_search", "max_uses": 5}]
        if use_search else []
    )
    messages = [{"role": "user", "content": user}]

    for _ in range(20):  # safety cap on tool-use iterations
        kwargs: dict = dict(
            model=model, max_tokens=max_tokens, system=system, messages=messages
        )
        if tools:
            kwargs["tools"] = tools
        resp = client.messages.create(**kwargs)

        text_parts, tool_uses = [], []
        for block in resp.content:
            if hasattr(block, "text"):
                text_parts.append(block.text)
            if getattr(block, "type", "") == "tool_use":
                tool_uses.append(block)

        if resp.stop_reason == "end_turn" or not tool_uses:
            return "\n".join(text_parts)

        # Anthropic web_search is server-side; send empty tool_results to continue
        messages.append({"role": "assistant", "content": resp.content})
        messages.append({"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": tu.id, "content": ""}
            for tu in tool_uses
        ]})

    return "\n".join(text_parts)


# ---------------------------------------------------------------------------
# Gemini
# ---------------------------------------------------------------------------

def _call_gemini(system: str, user: str, use_search: bool, max_tokens: int) -> str:
    """
    Calls Gemini via google-generativeai SDK.
    Google Search grounding is native to Gemini 2.0+ models — no tool-use
    loop needed; the model returns a final answer with search results inline.

    For UC Berkeley: configure GEMINI_API_KEY with your Vertex AI / AI Studio
    key, or use Application Default Credentials (ADC) on GCP infrastructure.
    """
    import google.generativeai as genai

    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        genai.configure(api_key=api_key)
    # If no key, falls back to Application Default Credentials (GCP / Vertex AI)

    model_name = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")

    # Google Search grounding — handled server-side by Gemini 2.0+
    tools = [{"google_search": {}}] if use_search else None

    model = genai.GenerativeModel(
        model_name=model_name,
        system_instruction=system,
        generation_config={"max_output_tokens": max_tokens},
        tools=tools,
    )
    response = model.generate_content(user)
    return response.text
