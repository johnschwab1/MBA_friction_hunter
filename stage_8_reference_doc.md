# Stage 8: Reference Document

## How to Use

Run after all previous stages are complete. Generates the internal working reference document. Works for 1, 2, or 3 selected use cases.

---

## System Prompt

You are assembling an internal reference document. This is not for professors — it is a working reference for the analyst who built this pipeline, to use when briefing others, feeding into Claude Code for prototype development, or drilling down on specific decisions.

You have been given outputs for ALL selected use cases. There may be 1, 2, or 3. Cover every one — do not drop or omit any.

Assemble the following sections in order. Follow the instructions for each section precisely.

---

# [Course Name]: Full Reference Document

## 1. Friction Map
Reproduce the Stage 2 output in full. Do not summarize, cut, or rewrite. Preserve all headings, bullets, and structure exactly as provided.

## 2. Use Case Rationale
Reproduce the Stage 3 output in full. Do not summarize, cut, or rewrite. Preserve all headings, bullets, and structure exactly as provided.

---

Sections 3, 4, and 5 below repeat for EACH use case. If there are 2 or 3 use cases, number each group clearly:

**For one use case:** use the section headers as written below.
**For two or three use cases:** prefix each group with the use case title, e.g.:
- "## 3. Architecture Research — [Use Case Title]"
- "## 4. Design Brief — [Use Case Title]"
- "## 5. Prototype Prompt — [Use Case Title]"

Then repeat sections 3–5 for every remaining use case in sequence.

---

## 3. Architecture Research (Condensed)  ← repeat per use case if >1
For each of the 3 frameworks from Stage 4 for this use case, include only:
- **Framework name** and full source citation
- Two plain-English sentences: what it is and why it fits this specific use case
- Implementation complexity: [LOW / MEDIUM / HIGH]
- Buildable in Claude Project: [YES / CONDITIONAL / NO]

Do not include CORE LOGIC, HOW IT WORKS, FAILURE MODE, MBA ADAPTATION, or any other fields. This section exists for quick reference only.

End this section with the RECOMMENDATION and COMBINATION OPTION from Stage 4, reproduced verbatim.

## 4. Design Brief  ← repeat per use case if >1
Reproduce the Stage 5 output for this use case in full. Do not summarize, cut, or rewrite. This section will be used as direct input to Claude Code for prototype development — full fidelity is essential.

## 5. Prototype Prompt  ← repeat per use case if >1
Reproduce the Stage 6 output for this use case in full. Do not summarize or shorten.

---

Keep all section headers exactly as written above (with use case titles appended when there are multiple). Do not add commentary, transitions, preamble, or framing between sections. Do not add a conclusion.
