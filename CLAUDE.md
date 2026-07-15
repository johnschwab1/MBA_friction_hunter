# CLAUDE.md — MBA Friction Hunter

## What This Project Is
An 8-stage AI pipeline that analyzes MBA syllabi to find where AI creates
genuine learning value, then generates working prototype prompts professors
can paste directly into Claude/Gemini/ChatGPT. Built in Streamlit, deployed
via GitHub Codespaces.

## Pipeline Architecture
- Stage 1: Criteria layer (reference doc, not run directly)
- Stage 2: Friction Hunter — analyzes syllabus for AI intervention points
- Stage 3: Use Case Selector — approval loop, professor gives direction
- Stage 4: Architecture Hunter — finds 3 research frameworks per use case
- Stage 5: Design Brief — full brief per use case
- Stage 6: Prototype Generator — paste-ready prompt, no placeholders
- Stage 7: Professor Brief — leave-behind document, 1-3 use cases
- Stage 8: Reference Document — internal working doc for analyst/Claude Code

Stages 4-6 run automatically per selected use case after Stage 3 approval.
Stages 7-8 compile all selected use cases into unified documents.

## Key Files
- `app.py` — main Streamlit app, all pipeline logic
- `llm_client.py` — model-agnostic LLM client, do not break this
- `stage_N_*.md` — system prompts, each has a `## System Prompt` section
- `.streamlit/secrets.toml` — LOCAL ONLY, never commit, contains live API key
- `.friction_hunter_session.json` — auto-generated, never commit

## Working Style — Non-Negotiable
- **Always talk before changing code.** Reflect back the plan, wait for
  approval before touching any file.
- **No unrequested changes.** Fix what was asked, nothing else. No cleanup,
  no refactoring, no "while I'm in here."
- **No placeholders in prototype prompts.** Stage 6 must produce fully
  baked, paste-ready prompts. All course context filled in from pipeline
  materials. Session-variable content handled by having the AI ask the
  student at the start.

## Formatting Rules for Stage Prompts
Output format must use:
- `##` markdown headings for sections
- `**bold field:**` labels for fields
- Never ALL CAPS field labels (they render as giant bold text in Streamlit)

## Security Rules
- `.streamlit/secrets.toml` must never be staged or committed
- `.friction_hunter_session.json` must never be staged or committed
- Both are in `.gitignore` — verify this before any broad `git add`
- Repo is public — treat all committed files as publicly visible

## LLM / API Notes
- `web_search_20250305` is a server-side Anthropic tool — the client
  returns empty content `''` intentionally. Do not replace with a manual
  search library.
- Provider switchable via `LLM_PROVIDER` env var (anthropic/gemini)
- Model set via `ANTHROPIC_MODEL` in secrets

## Known Patterns and Past Fixes
- Streamlit `disabled=not widget_value` on buttons doesn't update reliably
  on first render — handle empty input in the click callback instead
- Multi-use-case outputs (stages 4-6) are dicts keyed by uc_idx (int) —
  JSON serialization requires string keys, deserialize back to int on load
- Stage 7 and 8 must cover ALL selected use cases — the LLM will drop
  extras if not explicitly instructed to cover every one

## What This Tool Actually Does
It finds where students are struggling to learn — not because the material
is hard, but because the course structure can't provide enough practice reps,
fast enough feedback, or content connected to their own context. It then
builds AI-facilitated workshops for those moments — not tools that do
student work, but tools that teach.

## Audit Note
Review and trim this file periodically. Remove rules that no longer apply.
A rule belongs here if the same mistake happened twice — not for one-off
corrections.
