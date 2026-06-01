# MBA Friction Hunter

A prompt flow for identifying where AI can meaningfully improve MBA and business school education — and for building prototypes worth showing a professor.

## What This Is

A six-stage pipeline that takes a professor's curriculum artifacts (syllabus, slide deck, course description) and outputs:
1. A friction map showing where and why students struggle
2. A prioritized set of AI use cases worth building
3. Architecture options grounded in learning science research
4. Testable design briefs for each use case
5. Working prototype system prompts, ready to deploy in a Claude Project

## How to Use It

Run each stage sequentially. Each stage's output is the input to the next.

**For a professor meeting:** Run Stages 1–5. Bring the design briefs (Stage 5 output) to the meeting. Show prototypes (Stage 6) only if the professor commits to a use case.

**For your own preparation:** Run all 6 stages before the meeting. If Stage 6 returns a HOLD or REDESIGN, drop that use case before the meeting — don't show a brief you can't back up with a working prototype.

## The Six Stages

| Stage | Input | Output |
|---|---|---|
| 1. Criteria Layer | Read first — it's the rubric | Scoring matrix + friction taxonomy |
| 2. Friction Hunter | Curriculum artifact (syllabus, deck, description) | Structured friction map |
| 3. Use Case Selector | Friction map | 2–4 prioritized use cases |
| 4. Architecture Hunter | One use case | 3 architecture options with recommendation |
| 5. Design Brief Generator | Use case + chosen architecture | One-page testable brief |
| 6. Prototype Generator | Design brief | Working system prompt + feasibility score |

Ready-to-use system prompt templates are in `/prompts/`.

## Key Design Principles

Embedded throughout every stage:

- **Germane load protection:** AI should never do the cognitive work for the student. It creates conditions for effortful production, not substitutes for it.
- **Retrieval-first:** Students produce answers before receiving AI feedback.
- **Scaffold fading:** Every AI interaction should plan to give less help over time.
- **No patronizing:** MBA students are high-agency. Prompts that over-explain or hedge will be ignored.
- **Steelman over adversarial:** Constructive stress-testing, not emotional confrontation. The AI is on the student's side — helping them fortify their argument, not defeat them.

## Source Research

This pipeline is grounded in:
- **Khanmigo / Khan Academy** — 7-step prompt engineering; Socratic method implementation
- **SocraticAI** (MIT, arxiv 2512.03501) — structured input → Socratic response; students progress from vague to sophisticated in 2–3 weeks
- **Stanford SCALE / EDF Framework** (arxiv 2602.01415) — adaptive scaffolding with measurable fading
- **Cognitive Load Theory** (Sweller), **Desirable Difficulties** (Bjork), **Deliberate Practice** (Ericsson)
- **MetaLadder** (arxiv 2503.14891) — analogical transfer via structural problem mapping
- **Agentic Workflow for Education** (arxiv 2504.20082, 2509.01517)

## Prototype Templates

| Template | Architecture | Best For |
|---|---|---|
| `socratic_partner.md` | Socratic State Machine | Reasoning Opacity, conceptual depth |
| `steelman_partner.md` | Collaborative Stress-Test | High-stakes argumentation, case presentations |
| `worked_example_fader.md` | Worked Example Fading | Repetition Deficit, procedural skill building |
| `analogical_transfer.md` | Case-Based Analogical Mapping | Transfer Failure, cross-domain application |
| `retrieval_practice_loop.md` | Retrieval Practice + Spaced Testing | Feedback Latency, retention of frameworks |
