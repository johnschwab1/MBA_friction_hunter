# Stage 1: Criteria Layer

This is the foundation of the pipeline. Read before running Stage 2. It is not a prompt — it is the rubric that informs everything downstream.

---

## The Core Question

Not "can AI do this?" but: **"Is this friction AI should remove, or friction that produces learning?"**

Cognitive load theory distinguishes two kinds of difficulty:
- **Extraneous load** — burden from poor instructional design: slow feedback cycles, insufficient repetition, generic case studies, mechanical procedures repeated at the cost of faculty time. AI should eliminate this.
- **Germane load** — effortful production that builds lasting understanding: wrestling with a hard concept, constructing an argument under pressure, applying a framework in a novel context. AI must protect this, not replace it.

The screener's job is to find high-extraneous, low-germane modules.

---

## Friction Taxonomy

Before scoring any module, classify its dominant friction type. This determines the architecture category you'll search in Stage 4.

| Friction Type | What's Actually Happening | Detectable In Syllabus By |
|---|---|---|
| **Feedback Latency** | Students wait days or weeks for correction; the learning loop is broken | Graded assignments returned at next class; no structured in-class practice loops |
| **Repetition Deficit** | The skill needs 15–20 reps to internalize; the course provides 2–3 | "Students will practice X" — once; role plays described as single sessions |
| **Context Poverty** | Frameworks are taught on fixed case studies that feel detached from the student's actual work | "HBS case" with no mechanism for the student to apply it to their own company or industry |
| **Reasoning Opacity** | Students produce outputs (reports, analyses) but never articulate or examine their thinking process | Graded on deliverables only; no structured self-explanation requirement |
| **Transfer Failure** | Students can execute a framework in the taught format but fail in novel situations | All examples in the same domain or industry throughout the module; no structured variation |

A module can have multiple friction types. Score and note the dominant one. Modules with Transfer Failure as the primary type require a more careful architecture — do not shortcut them.

---

## AI Suitability Scoring Matrix

Score each module 1–3 on each dimension. Maximum score: 15.

| Dimension | 3 — High AI Fit | 2 — Moderate | 1 — Low AI Fit |
|---|---|---|---|
| **Teaching Format** | Unidirectional delivery; static knowledge check; professor repeating identical content each cohort | Blended — some discussion, some delivery | Live social synthesis; peer critique; case negotiation requiring real-time reading of the room |
| **Feedback Requirement** | High-volume, iterative, calibrated feedback — more than a professor can provide at scale | Needs feedback but at manageable volume | Requires nuanced judgment about subjective quality, tone, or interpersonal dynamics |
| **Contextual Salience** | Learning is substantially enhanced by injecting the student's own company, market, or role | Some personalization helps but isn't decisive | Relies on shared historical case where the specific facts and narrative are the learning object |
| **Learning Mode** | Individual analytical work; pattern recognition; structured linear reasoning | Mixed individual and social | Collaborative negotiation; multi-stakeholder synthesis; social accountability dynamics |
| **Friction Tractability** | Feedback Latency or Repetition Deficit — cleanest AI fits, well-validated architectures exist | Context Poverty or Reasoning Opacity — strong fits but require careful prompt design | Transfer Failure — possible but requires analogical architecture; do not use retrieval or Socratic patterns alone |

**Score interpretation:**
- **13–15:** Strong AI candidate. Move to Stage 2 immediately.
- **9–12:** Moderate candidate. Check the friction type — if Transfer Failure is dominant, require strong architecture justification before prototyping.
- **Below 9:** Low priority for this round. Flag for future consideration.

---

## What NOT to AI-ify

Screen these out explicitly before scoring:

1. **Germane load masquerading as extraneous load.** If a module is hard and students complain, that is not evidence it's AI-ready. Ask: is the difficulty building a durable schema? If yes, protect it.

2. **Learning where the friction is the lesson.** Live negotiation workshops, multi-stakeholder conflict simulations, team dynamics exercises — the social friction is the pedagogy. Removing it removes the learning.

3. **Modules where the case specifics are the learning object.** If students are meant to learn from a particular story, its details, its ambiguities — AI-generated variation undermines the point. Use AI for practice around the case, not as a case substitute.

---

## Deployment Viability Check

Run this separately from the pedagogical scoring. It determines prioritization, not selection.

| Signal | Green | Yellow | Red |
|---|---|---|---|
| Faculty posture | "AI could amplify what I do" | Curious but skeptical | "AI threatens what I do" |
| Institutional access | LLM tools approved and student-accessible | Under institutional review | Blocked or unknown policy |
| Module ownership | Faculty owns and can modify freely | Shared ownership | Locked or committee-controlled |
| Time horizon | Upcoming semester | Mid-semester | Already delivered |

Any single Red is a deprioritization signal for this cycle, not a permanent rejection.
