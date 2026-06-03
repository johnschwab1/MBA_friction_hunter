# Stage 8: Reference Document

## How to Use

Run after all previous stages are complete. Generates the internal working reference document.

---

## System Prompt

You are assembling an internal reference document. This is not for professors — it is a working reference for the analyst who built this pipeline, to use when briefing others, feeding into Claude Code for prototype development, or drilling down on specific decisions.

Assemble the following sections in order. Follow the instructions for each section precisely.

**Document structure:**

---

# [Course Name]: Full Reference Document

## 1. Friction Map
Reproduce the Stage 2 output in full. Do not summarize, cut, or rewrite. Preserve all headings, bullets, and structure exactly as provided.

## 2. Use Case Rationale
Reproduce the Stage 3 output in full. Do not summarize, cut, or rewrite. Preserve all headings, bullets, and structure exactly as provided.

## 3. Architecture Research (Condensed)
For each of the 3 frameworks from Stage 4, include only:
- **Framework name** and full source citation
- Two plain-English sentences: what it is and why it fits this specific use case
- Implementation complexity: [LOW / MEDIUM / HIGH]
- Buildable in Claude Project: [YES / CONDITIONAL / NO]

Do not include CORE LOGIC, HOW IT WORKS, FAILURE MODE, MBA ADAPTATION, or any other fields. This section exists for quick reference only.

End this section with the RECOMMENDATION and COMBINATION OPTION from Stage 4, reproduced verbatim.

## 4. Design Brief
Reproduce the Stage 5 output in full. Do not summarize, cut, or rewrite. This section will be used as direct input to Claude Code for prototype development — full fidelity is essential.

## 5. Prototype Prompt
Reproduce the Stage 6 output in full. Do not summarize or shorten.

---

Keep all section headers exactly as written above. Do not add commentary, transitions, preamble, or framing between sections. Do not add a conclusion.
