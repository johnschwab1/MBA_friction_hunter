# Learning Breakthrough Workshop Builder

*Finds where students get stuck on any subject, and builds the AI workshop to get them unstuck.*

## What This Is

An 8-stage pipeline that takes any curriculum artifact — syllabus, slide deck, course description, training manual, article — and outputs:

1. A friction map showing where and why students get stuck
2. A prioritized set of AI workshop opportunities worth building
3. Architecture options grounded in learning science research
4. Testable design briefs for each opportunity
5. Working prototype prompts, ready to paste into Claude, Gemini, or ChatGPT
6. A leave-behind brief for the instructor
7. A full reference document for deeper development

Works for any subject, any audience: higher education, corporate training, professional development, bootcamps, K-12.

## How to Use It

Run each stage sequentially. Each stage's output feeds the next. The Streamlit app automates stages 4-8 after you confirm your use cases.

**For an instructor meeting:** Run Stages 1-5. Bring the design briefs to the meeting. Show prototypes only if the instructor commits to a use case.

**For your own preparation:** Run all 8 stages before the meeting. If Stage 6 returns a HOLD or REDESIGN, drop that use case before the meeting.

## The Eight Stages

| Stage | Input | Output |
|---|---|---|
| 1. Criteria Layer | Read first — it's the rubric | Scoring matrix + friction taxonomy |
| 2. Friction Hunter | Curriculum artifact (syllabus, deck, description) | Structured friction map |
| 3. Use Case Selector | Friction map | 2-4 prioritized use cases |
| 4. Architecture Hunter | One use case | 3 architecture options with recommendation |
| 5. Design Brief Generator | Use case + chosen architecture | Full testable brief |
| 6. Prototype Generator | Design brief | Working system prompt + feasibility score |
| 7. Instructor Brief | All selected use cases | Leave-behind document with prompts |
| 8. Reference Document | All selected use cases | Full working reference for development |

## Key Design Principles

- **Germane load protection:** AI should never do the cognitive work for the student. It creates conditions for effortful production, not substitutes for it.
- **Retrieval-first:** Students produce answers before receiving AI feedback.
- **Scaffold fading:** Every AI interaction should plan to give less help over time.
- **No placeholders:** Every generated prototype prompt is paste-ready — no editing required before use.
- **Steelman over adversarial:** Constructive stress-testing, not emotional confrontation.

## Source Research

This pipeline is grounded in:
- **Khanmigo / Khan Academy** — Socratic method implementation
- **SocraticAI** (MIT, arxiv 2512.03501) — structured Socratic dialogue
- **Stanford SCALE / EDF Framework** (arxiv 2602.01415) — adaptive scaffolding with measurable fading
- **Cognitive Load Theory** (Sweller), **Desirable Difficulties** (Bjork), **Deliberate Practice** (Ericsson)
- **MetaLadder** (arxiv 2503.14891) — analogical transfer via structural problem mapping
- **Agentic Workflow for Education** (arxiv 2504.20082, 2509.01517)

## Setup

1. Clone this repo
2. Install dependencies: `pip install -r requirements.txt`
3. Create `.streamlit/secrets.toml` (see `.streamlit/secrets.toml.example`)
4. Run: `streamlit run app.py`
