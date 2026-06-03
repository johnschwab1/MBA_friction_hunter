"""
MBA Friction Hunter — Streamlit App

Local dev:
  streamlit run app.py

Deploy to Streamlit Cloud:
  1. Push this repo to GitHub
  2. Connect at share.streamlit.io
  3. Add secrets in the dashboard (see .streamlit/secrets.toml.example)

Provider switching:
  Set LLM_PROVIDER = "anthropic" or "gemini" in your secrets file.
"""

import io
import json
import os
import re
from pathlib import Path

import streamlit as st

# ── Bootstrap secrets ──
for _k in ["ANTHROPIC_API_KEY", "ANTHROPIC_MODEL", "GEMINI_API_KEY", "GEMINI_MODEL", "LLM_PROVIDER"]:
    if _k in st.secrets:
        os.environ[_k] = st.secrets[_k]

from llm_client import call_llm, provider_label  # noqa: E402

st.set_page_config(page_title="MBA Friction Hunter", page_icon="🎓", layout="wide", initial_sidebar_state="collapsed")

REPO_ROOT = Path(__file__).parent
STAGE_NAMES = {
    2: "Friction Hunter", 3: "Use Case Selector", 4: "Architecture Hunter",
    5: "Design Brief", 6: "Prototype", 7: "Professor Brief", 8: "Reference Document"
}
STAGE_FILES = {
    2: "stage_2_friction_hunter.md", 3: "stage_3_use_case_selector.md",
    4: "stage_4_architecture_hunter.md", 5: "stage_5_design_brief_generator.md",
    6: "stage_6_prototype_generator.md",
    7: "stage_7_professor_brief.md", 8: "stage_8_reference_doc.md",
}
STAGE_SLUGS = {
    2: "friction_hunter", 3: "use_case_selector", 4: "architecture_hunter",
    5: "design_brief", 6: "prototype", 7: "professor_brief", 8: "reference_document"
}
SEARCH_STAGES = {4}
UC_STAGES = {4, 5, 6}  # stages that run once per selected use case

_FAIL_PHRASES = [
    "i notice that", "i cannot", "i'm unable", "i am unable",
    "unable to find", "unable to access", "unable to retrieve",
    "don't have access", "do not have access",
    "no public syllabus", "no publicly available",
    "search results don't contain", "search results do not contain",
    "not find the full text", "couldn't find", "could not find",
    "not publicly available", "not available online",
    "i don't see", "i do not see",
]


def _looks_like_syllabus(text: str) -> bool:
    if len(text) < 500:
        return False
    preview = text[:600].lower()
    return not any(phrase in preview for phrase in _FAIL_PHRASES)


# ── Session state ──
for _k, _v in {
    "syllabus": "", "outputs": {}, "stage": 0,
    "search_results": "", "search_fetched": False, "search_valid": None,
    "stage3_direction": "", "stage3_examples": "",
    "profile_mode": False, "profile_result": "",
    # use-case selection
    "use_cases_extracted": [],   # [{"title": str, "text": str}, ...]
    "selected_use_cases": [],    # [int, ...] indices into use_cases_extracted
    "use_cases_confirmed": False,
}.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


# ── Helpers ──

def extract_system_prompt(filename: str) -> str:
    text = (REPO_ROOT / filename).read_text()
    match = re.search(r"## System Prompt\s*\n(.*)", text, re.DOTALL)
    if not match:
        raise ValueError(f"No '## System Prompt' section in {filename}")
    return match.group(1).strip()


@st.cache_data(show_spinner=False)
def load_criteria() -> str:
    return (REPO_ROOT / "stage_1_criteria_layer.md").read_text()


def parse_uploaded_file(f) -> str:
    ext = f.name.rsplit(".", 1)[-1].lower()
    if ext == "pdf":
        import pdfplumber
        with pdfplumber.open(io.BytesIO(f.read())) as pdf:
            return "\n\n".join(page.extract_text() or "" for page in pdf.pages)
    if ext == "docx":
        import docx
        doc = docx.Document(io.BytesIO(f.read()))
        return "\n".join(p.text for p in doc.paragraphs)
    if ext == "pptx":
        from pptx import Presentation
        prs = Presentation(io.BytesIO(f.read()))
        slides = []
        for i, slide in enumerate(prs.slides, 1):
            texts = [s.text.strip() for s in slide.shapes if hasattr(s, "text") and s.text.strip()]
            if texts:
                slides.append(f"[Slide {i}]\n" + "\n".join(texts))
        return "\n\n".join(slides)
    return f.read().decode("utf-8", errors="replace")


def extract_use_cases_from_stage3(stage3_output: str) -> list:
    """Call LLM to extract use case titles + text from Stage 3 output. Returns [{title, text}]."""
    system = (
        "Extract the distinct use cases from this MBA course AI analysis output. "
        "Return ONLY a valid JSON array. Each element must have exactly two fields: "
        "'title' (the short name of the use case, 1 line) and "
        "'text' (the complete description of that use case as it appears in the document, preserving all detail). "
        "Return raw JSON only — no markdown fences, no explanation, no other text."
    )
    raw = call_llm(system, stage3_output, max_tokens=3000)
    # Find JSON array in response
    match = re.search(r"\[.*\]", raw, re.DOTALL)
    if match:
        try:
            result = json.loads(match.group())
            if isinstance(result, list) and all("title" in r and "text" in r for r in result):
                return result
        except json.JSONDecodeError:
            pass
    # Fallback: treat entire Stage 3 output as one use case
    return [{"title": "All Use Cases", "text": stage3_output}]


def build_uc_user_msg(active: int, uc_idx: int) -> str:
    uc = st.session_state.use_cases_extracted[uc_idx]
    if active == 4:
        return f"USE CASE TO ANALYZE:\n\n{uc['text']}"
    if active == 5:
        return (
            f"USE CASE:\n\n{uc['text']}\n\n---\n\n"
            f"ARCHITECTURE RECOMMENDATIONS:\n\n{st.session_state.outputs[4][uc_idx]}"
        )
    if active == 6:
        return st.session_state.outputs[5][uc_idx]
    return ""


def build_report_user_msg() -> str:
    """Build the combined user message for Stages 7 and 8."""
    outputs = st.session_state.outputs
    selected = st.session_state.selected_use_cases
    uc_list = st.session_state.use_cases_extracted
    sections = []
    for uc_idx in selected:
        uc = uc_list[uc_idx]
        sections.append(
            f"=== USE CASE: {uc['title']} ===\n\n"
            f"USE CASE DESCRIPTION:\n{uc['text']}\n\n"
            f"ARCHITECTURE RESEARCH:\n{outputs.get(4, {}).get(uc_idx, '')}\n\n"
            f"DESIGN BRIEF:\n{outputs.get(5, {}).get(uc_idx, '')}\n\n"
            f"PROTOTYPE PROMPT:\n{outputs.get(6, {}).get(uc_idx, '')}"
        )
    return (
        f"FRICTION MAP (Stage 2):\n\n{outputs.get(2, '')}\n\n---\n\n"
        f"ALL SELECTED USE CASES:\n\n" + "\n\n---\n\n".join(sections)
    )


def dict_output_to_md(stage_num: int, output_dict: dict) -> str:
    """Flatten a per-use-case dict output to a single markdown string for download."""
    uc_list = st.session_state.use_cases_extracted
    parts = []
    for uc_idx, text in output_dict.items():
        title = uc_list[uc_idx]["title"] if uc_idx < len(uc_list) else f"Use Case {uc_idx + 1}"
        parts.append(f"# {title}\n\n{text}")
    return "\n\n---\n\n".join(parts)


def _add_runs_with_bold(paragraph, text: str):
    parts = text.split("**")
    for i, part in enumerate(parts):
        if part:
            run = paragraph.add_run(part)
            run.bold = (i % 2 == 1)


def _add_markdown_to_doc(doc, text: str):
    for line in text.split("\n"):
        s = line.rstrip()
        if s.startswith("### "):
            doc.add_heading(s[4:], level=3)
        elif s.startswith("## "):
            doc.add_heading(s[3:], level=2)
        elif s.startswith("# "):
            doc.add_heading(s[2:], level=1)
        elif s.startswith("- ") or s.startswith("* "):
            p = doc.add_paragraph(style="List Bullet")
            _add_runs_with_bold(p, s[2:])
        elif re.match(r"^\d+\. ", s):
            p = doc.add_paragraph(style="List Number")
            _add_runs_with_bold(p, re.sub(r"^\d+\. ", "", s))
        elif s == "---":
            doc.add_paragraph("─" * 60)
        elif s == "":
            pass
        else:
            p = doc.add_paragraph()
            _add_runs_with_bold(p, s)


def generate_report_docx(professor_brief: str, reference_doc: str) -> bytes:
    from docx import Document
    doc = Document()
    _add_markdown_to_doc(doc, professor_brief)
    doc.add_page_break()
    _add_markdown_to_doc(doc, reference_doc)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def reset():
    for k, v in {
        "syllabus": "", "outputs": {}, "stage": 0,
        "search_results": "", "search_fetched": False, "search_valid": None,
        "stage3_direction": "", "stage3_examples": "",
        "profile_mode": False, "profile_result": "",
        "use_cases_extracted": [], "selected_use_cases": [], "use_cases_confirmed": False,
    }.items():
        st.session_state[k] = v
    st.rerun()


def reset_search():
    st.session_state.search_results = ""
    st.session_state.search_fetched = False
    st.session_state.search_valid = None
    st.session_state.syllabus = ""
    st.session_state.profile_mode = False
    st.session_state.profile_result = ""


# ── Header ──
col_title, col_badge = st.columns([5, 1])
with col_title:
    st.title("🎓 MBA Friction Hunter")
    st.caption("Find where AI creates genuine learning value in an MBA curriculum — then build a working prototype.")
with col_badge:
    st.markdown(f"<br><span style='font-size:0.8em;color:gray'>🤖 {provider_label()}</span>", unsafe_allow_html=True)

st.divider()


# ═══════════════════════════════════════════
# INTAKE
# ═══════════════════════════════════════════

if st.session_state.stage == 0:
    st.subheader("Step 1 — Load the Syllabus")
    tab_search, tab_upload, tab_paste = st.tabs(["🔍  Search the web", "📁  Upload a file", "📝  Paste text"])

    with tab_search:
        st.caption("Search for a publicly available syllabus. You'll see a list of options before we fetch the full text.")

        if st.session_state.profile_mode:
            st.info(
                "**Building a course profile from public information.**\n\n"
                "Enter the professor's name and course title and I'll search for their research, "
                "course descriptions, and typical MBA course structure to build a working profile."
            )
            prof_name = st.text_input("Professor name", placeholder="e.g. Mathijs de Vaan", key="prof_name_input")
            course_name = st.text_input("Course name / topic", placeholder="e.g. Leading People — Haas MBA", key="course_name_input")
            col_build, col_back = st.columns([2, 2])
            with col_build:
                if st.button("Build profile →", type="primary", disabled=not (prof_name.strip() and course_name.strip())):
                    with st.spinner("Searching for professor and course information…"):
                        profile_system = (
                            "You are a research assistant helping analyze an MBA course for AI integration opportunities. "
                            "The professor's syllabus is not publicly available, so you need to construct a usable course profile. "
                            "Search for: (1) the professor's published research, teaching philosophy, and areas of expertise; "
                            "(2) the school's official course description and learning objectives; "
                            "(3) typical structure and content of MBA courses on this topic at peer institutions. "
                            "Synthesize this into a structured course profile with these sections:\n"
                            "- Professor Background & Expertise\n- Course Overview & Learning Objectives\n"
                            "- Likely Topics & Weekly Structure (inferred)\n"
                            "- Key Assignments & Assessments (typical for this course type)\n"
                            "- Pedagogical Approach (based on professor's research and known teaching style)\n"
                            "Be specific and cite sources where found. Label inferred content clearly as '[Inferred]'."
                        )
                        st.session_state.profile_result = call_llm(
                            profile_system,
                            f"Professor: {prof_name.strip()}\nCourse: {course_name.strip()}",
                            use_search=True, max_tokens=3000
                        )
                    st.rerun()
            with col_back:
                if st.button("← Back to search"):
                    reset_search()
                    st.rerun()
            if st.session_state.profile_result:
                st.success(f"✓ Profile built — {len(st.session_state.profile_result):,} chars")
                with st.expander("Preview course profile", expanded=True):
                    st.markdown(st.session_state.profile_result[:2000] +
                                ("\n\n*[truncated — full content will be used for analysis]*"
                                 if len(st.session_state.profile_result) > 2000 else ""))
                st.caption("⚠️ This is a synthesized profile, not the actual syllabus. The analysis will reflect that.")
                if st.button("Start analysis with this profile →", type="primary"):
                    st.session_state.syllabus = st.session_state.profile_result
                    st.session_state.stage = 2
                    st.rerun()
        else:
            q_col, btn_col = st.columns([4, 1])
            with q_col:
                query = st.text_input("Query", placeholder="e.g. Haas MBA marketing 2025",
                                      label_visibility="collapsed", key="search_query")
            with btn_col:
                do_search = st.button("Search →", use_container_width=True)
            if do_search and query:
                with st.spinner(f"Searching for '{query}'…"):
                    find_system = ("You are a research assistant. Search for MBA course syllabi matching the user's query. "
                                   "Return a numbered list of up to 5 options. For each: number, title, school, year, "
                                   "and one-sentence description. Format: N. Title — School (Year): Description")
                    st.session_state.search_results = call_llm(find_system, f"Find MBA syllabi for: {query}",
                                                               use_search=True, max_tokens=800)
                    st.session_state.search_fetched = False
                    st.session_state.search_valid = None
            if st.session_state.search_results:
                st.markdown(st.session_state.search_results)
                st.divider()
                if st.session_state.search_fetched and st.session_state.search_valid is False:
                    st.warning("**No public syllabus found.**\n\nThe search couldn't retrieve the actual syllabus text — "
                               "it may not be publicly available. Choose how to proceed:")
                    with st.expander("See what was returned"):
                        st.text(st.session_state.syllabus[:800] + "…")
                    r_col, p_col, m_col = st.columns(3)
                    with r_col:
                        st.markdown("**Option 1: Try again**")
                        if st.button("🔄 New search query", use_container_width=True):
                            reset_search(); st.rerun()
                    with p_col:
                        st.markdown("**Option 2: Build a profile**")
                        if st.button("🧠 Build from public info", use_container_width=True):
                            st.session_state.profile_mode = True; st.rerun()
                    with m_col:
                        st.markdown("**Option 3: Manual input**")
                        st.caption("Switch to the Upload or Paste tab above.")
                elif not st.session_state.search_fetched:
                    pick_col, fetch_col = st.columns([1, 3])
                    with pick_col:
                        pick = st.number_input("Which result?", min_value=1, max_value=5, step=1)
                    with fetch_col:
                        if st.button("Fetch full syllabus →", use_container_width=True):
                            with st.spinner("Fetching full syllabus…"):
                                fetched = call_llm(
                                    "You are a research assistant. From the search results provided, fetch the full "
                                    "text of the selected option. Return only the complete syllabus content: course "
                                    "description, learning objectives, weekly schedule, assignments, and readings.",
                                    f"Results:\n\n{st.session_state.search_results}\n\nFetch full text of option {pick}.",
                                    use_search=True, max_tokens=4096
                                )
                            st.session_state.syllabus = fetched
                            st.session_state.search_fetched = True
                            st.session_state.search_valid = _looks_like_syllabus(fetched)
                            st.rerun()
                elif st.session_state.search_valid:
                    st.success(f"✓ Fetched {len(st.session_state.syllabus):,} chars")
                    with st.expander("Preview fetched syllabus"):
                        st.text(st.session_state.syllabus[:1000] + "…")
                    c1, c2 = st.columns([2, 2])
                    with c1:
                        if st.button("Start analysis →", type="primary", key="search_go"):
                            st.session_state.stage = 2; st.rerun()
                    with c2:
                        if st.button("🔄 Try a different result"):
                            st.session_state.search_fetched = False
                            st.session_state.search_valid = None
                            st.session_state.syllabus = ""
                            st.rerun()

    with tab_upload:
        st.caption("PDF, DOCX, PPTX, and TXT supported. For Google Docs or Slides: export as PDF first.")
        uploaded = st.file_uploader("File", type=["pdf", "docx", "pptx", "txt"], label_visibility="collapsed")
        if uploaded:
            with st.spinner("Parsing file…"):
                parsed = parse_uploaded_file(uploaded)
            st.success(f"✓ {uploaded.name} — {len(parsed):,} chars")
            with st.expander("Preview"):
                st.text(parsed[:1000] + ("..." if len(parsed) > 1000 else ""))
            if st.button("Start analysis →", type="primary", key="upload_go"):
                st.session_state.syllabus = parsed
                st.session_state.stage = 2
                st.rerun()

    with tab_paste:
        st.caption("Paste the syllabus text directly.")
        pasted = st.text_area("Text", height=320, placeholder="Paste your syllabus here…", label_visibility="collapsed")
        if st.button("Start analysis →", type="primary", key="paste_go") and pasted.strip():
            st.session_state.syllabus = pasted.strip()
            st.session_state.stage = 2
            st.rerun()


# ═══════════════════════════════════════════
# PIPELINE (stages 2–8)
# ═══════════════════════════════════════════

elif st.session_state.stage >= 2:
    criteria = load_criteria()

    if st.button("↩ New syllabus"):
        reset()

    # ── Completed stages (collapsed) ──
    for s in range(2, st.session_state.stage):
        if s not in st.session_state.outputs:
            continue
        with st.expander(f"✅ Stage {s}: {STAGE_NAMES[s]}", expanded=False):
            output = st.session_state.outputs[s]
            if isinstance(output, dict):
                uc_list = st.session_state.use_cases_extracted
                done_indices = [i for i in st.session_state.selected_use_cases if i in output]
                if done_indices:
                    tabs = st.tabs([uc_list[i]["title"] for i in done_indices])
                    for tab, uc_idx in zip(tabs, done_indices):
                        with tab:
                            st.markdown(output[uc_idx])
                            st.download_button(
                                label="Download .md",
                                data=output[uc_idx],
                                file_name=f"stage_{s:02d}_{STAGE_SLUGS[s]}_{uc_idx}.md",
                                mime="text/markdown",
                                key=f"dl_done_{s}_{uc_idx}"
                            )
            else:
                st.markdown(output)
                st.download_button(label="Download .md", data=output,
                    file_name=f"stage_{s:02d}_{STAGE_SLUGS[s]}.md", mime="text/markdown",
                    key=f"dl_done_{s}")

    active = st.session_state.stage

    if active <= 8:
        st.subheader(f"Stage {active}: {STAGE_NAMES[active]}")
        if active == 4:
            st.caption("🔍 Web search active — finding current research and frameworks for each use case")
        if active == 7:
            st.caption("📄 Generating Professor Brief — the leave-behind document")
        if active == 8:
            st.caption("📋 Assembling Reference Document — your internal working document")

        # ═══════════════════════════════════════════
        # STAGE 2: Friction Hunter (single run)
        # ═══════════════════════════════════════════
        if active == 2:
            if 2 not in st.session_state.outputs:
                if st.button("Run Stage 2 →", type="primary"):
                    system = extract_system_prompt(STAGE_FILES[2])
                    user_msg = (f"CRITERIA REFERENCE:\n\n{criteria}\n\n---\n\n"
                                f"CURRICULUM TO ANALYZE:\n\n{st.session_state.syllabus}")
                    with st.spinner("Friction Hunter…"):
                        st.session_state.outputs[2] = call_llm(system, user_msg)
                    st.rerun()
            else:
                st.markdown(st.session_state.outputs[2])
                st.divider()
                a_col, dl_col, _ = st.columns([2, 2, 3])
                with a_col:
                    if st.button("↺ Re-run Stage 2"):
                        del st.session_state.outputs[2]; st.rerun()
                with dl_col:
                    st.download_button("Download .md", data=st.session_state.outputs[2],
                        file_name="stage_02_friction_hunter.md", mime="text/markdown", key="dl_active_2")
                if st.button("Continue to Stage 3 →", type="primary"):
                    st.session_state.stage = 3; st.rerun()

        # ═══════════════════════════════════════════
        # STAGE 3: Use Case Selector + approval loop + use case selection
        # ═══════════════════════════════════════════
        elif active == 3:
            if 3 not in st.session_state.outputs:
                if st.button("Run Stage 3 →", type="primary"):
                    system = extract_system_prompt(STAGE_FILES[3])
                    base = st.session_state.outputs.get(2, st.session_state.syllabus)
                    d = st.session_state.stage3_direction
                    user_msg = f"{base}\n\nDIRECTION FROM PROFESSOR:\n{d}" if d else base
                    with st.spinner("Use Case Selector…"):
                        st.session_state.outputs[3] = call_llm(system, user_msg)
                    st.rerun()
            else:
                st.markdown(st.session_state.outputs[3])
                st.divider()

                # ── Use case selection (after Satisfied is clicked and use cases extracted) ──
                if st.session_state.use_cases_extracted and not st.session_state.use_cases_confirmed:
                    st.subheader("☑️ Choose which use cases to develop")
                    st.caption("Select any or all. Each selected use case will go through Architecture, Design Brief, and Prototype stages.")
                    selected = []
                    for i, uc in enumerate(st.session_state.use_cases_extracted):
                        if st.checkbox(uc["title"], value=True, key=f"uc_check_{i}"):
                            selected.append(i)
                    st.divider()
                    c1, c2 = st.columns([2, 3])
                    with c1:
                        confirm_disabled = len(selected) == 0
                        if st.button(f"Develop {len(selected)} use case(s) →", type="primary", disabled=confirm_disabled):
                            st.session_state.selected_use_cases = selected
                            st.session_state.use_cases_confirmed = True
                            st.session_state.stage = 4
                            st.rerun()
                    with c2:
                        if st.button("↺ Re-run Stage 3 with new direction"):
                            st.session_state.use_cases_extracted = []
                            del st.session_state.outputs[3]
                            st.session_state.stage3_examples = ""
                            st.rerun()

                # ── Approval loop (before extraction) ──
                elif not st.session_state.use_cases_extracted:
                    if not st.session_state.stage3_examples:
                        with st.spinner("Generating guidance suggestions…"):
                            ex_system = (
                                "Based on these MBA course AI use case recommendations, write 3-4 short, specific "
                                "examples of direction a professor might give to improve or redirect the selection. "
                                "Make each concrete and tied to the actual use cases shown — reference specific "
                                "course elements, weeks, or assignments by name. "
                                "Format as a markdown bulleted list. Each should be one complete actionable sentence."
                            )
                            st.session_state.stage3_examples = call_llm(
                                ex_system, f"Use cases:\n\n{st.session_state.outputs[3]}", max_tokens=400
                            )
                    st.info("💡 **Not sure what to change? Here are examples of useful direction:**\n\n"
                            + st.session_state.stage3_examples)
                    direction_input = st.text_area(
                        "Give me direction and I'll re-run — or leave blank and click Satisfied:",
                        placeholder="e.g. 'The negotiation simulation in week 7 is the hardest part — center the use cases there instead'",
                        key="stage3_direction_input", height=100,
                    )
                    col1, col2, col3 = st.columns([2, 2, 2])
                    with col1:
                        if st.button("↺ Re-run with this direction", disabled=not direction_input.strip()):
                            st.session_state.stage3_direction = direction_input.strip()
                            st.session_state.stage3_examples = ""
                            del st.session_state.outputs[3]
                            st.rerun()
                    with col2:
                        if st.button("✓ Satisfied — Choose use cases →", type="primary"):
                            with st.spinner("Extracting use cases…"):
                                st.session_state.use_cases_extracted = extract_use_cases_from_stage3(
                                    st.session_state.outputs[3]
                                )
                            st.session_state.stage3_direction = ""
                            st.rerun()
                    with col3:
                        st.download_button(label="Download .md", data=st.session_state.outputs[3],
                            file_name="stage_03_use_case_selector.md", mime="text/markdown", key="dl_stage3")

        # ═══════════════════════════════════════════
        # STAGES 4-6: per-use-case, displayed in tabs
        # ═══════════════════════════════════════════
        elif active in UC_STAGES:
            selected = st.session_state.selected_use_cases
            uc_list = st.session_state.use_cases_extracted
            current_outputs = st.session_state.outputs.get(active, {})
            all_done = all(i in current_outputs for i in selected)

            tabs = st.tabs([uc_list[i]["title"] for i in selected])
            for tab, uc_idx in zip(tabs, selected):
                with tab:
                    if uc_idx in current_outputs:
                        st.markdown(current_outputs[uc_idx])
                        st.divider()
                        r_col, dl_col, _ = st.columns([2, 2, 3])
                        with r_col:
                            if st.button("↺ Re-run", key=f"rerun_{active}_{uc_idx}"):
                                st.session_state.outputs[active].pop(uc_idx, None)
                                st.rerun()
                        with dl_col:
                            st.download_button(
                                label="Download .md",
                                data=current_outputs[uc_idx],
                                file_name=f"stage_{active:02d}_{STAGE_SLUGS[active]}_{uc_idx}.md",
                                mime="text/markdown",
                                key=f"dl_{active}_{uc_idx}"
                            )
                    else:
                        st.caption(f"Ready to run for: **{uc_list[uc_idx]['title']}**")
                        if st.button(f"Run Stage {active} →", type="primary", key=f"run_{active}_{uc_idx}"):
                            system = extract_system_prompt(STAGE_FILES[active])
                            user_msg = build_uc_user_msg(active, uc_idx)
                            with st.spinner(f"{STAGE_NAMES[active]}…"):
                                result = call_llm(system, user_msg, use_search=(active in SEARCH_STAGES))
                            if active not in st.session_state.outputs:
                                st.session_state.outputs[active] = {}
                            st.session_state.outputs[active][uc_idx] = result
                            st.rerun()

            st.divider()
            if all_done:
                if st.button(f"Continue to Stage {active + 1} →", type="primary"):
                    st.session_state.stage = active + 1
                    st.rerun()
            else:
                remaining = sum(1 for i in selected if i not in current_outputs)
                st.caption(f"{remaining} use case(s) still need to be run above before continuing.")

        # ═══════════════════════════════════════════
        # STAGES 7-8: report generation
        # ═══════════════════════════════════════════
        elif active in (7, 8):
            if active not in st.session_state.outputs:
                if st.button(f"Run Stage {active} →", type="primary"):
                    system = extract_system_prompt(STAGE_FILES[active])
                    with st.spinner(f"{STAGE_NAMES[active]}…"):
                        result = call_llm(system, build_report_user_msg())
                    st.session_state.outputs[active] = result
                    st.rerun()
            else:
                st.markdown(st.session_state.outputs[active])
                st.divider()

                if active == 8:
                    # ── Pipeline complete ──
                    st.success("🏁 Pipeline complete!")
                    st.subheader("📥 Download Report")
                    if 7 in st.session_state.outputs:
                        docx_bytes = generate_report_docx(
                            st.session_state.outputs[7],
                            st.session_state.outputs[8]
                        )
                        dl1, dl2, dl3 = st.columns(3)
                        with dl1:
                            st.download_button(
                                label="📄 Full Report (.docx)",
                                data=docx_bytes,
                                file_name="mba_friction_hunter_report.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                type="primary"
                            )
                        with dl2:
                            st.download_button("Professor Brief (.md)", data=st.session_state.outputs[7],
                                file_name="professor_brief.md", mime="text/markdown")
                        with dl3:
                            st.download_button("Reference Doc (.md)", data=st.session_state.outputs[8],
                                file_name="reference_document.md", mime="text/markdown")
                        st.caption("💡 To open in Google Docs: upload the .docx to Google Drive, "
                                   "then right-click → Open with Google Docs.")
                    st.divider()
                    st.subheader("All Stage Outputs")
                    for s in range(2, 9):
                        if s not in st.session_state.outputs:
                            continue
                        output = st.session_state.outputs[s]
                        dl_data = dict_output_to_md(s, output) if isinstance(output, dict) else output
                        st.download_button(
                            label=f"Stage {s}: {STAGE_NAMES[s]}",
                            data=dl_data,
                            file_name=f"stage_{s:02d}_{STAGE_SLUGS[s]}.md",
                            mime="text/markdown",
                            key=f"dl_final_{s}"
                        )
                else:
                    a_col, dl_col, _ = st.columns([2, 2, 3])
                    with a_col:
                        if st.button("↺ Re-run Stage 7"):
                            del st.session_state.outputs[7]; st.rerun()
                    with dl_col:
                        st.download_button("Download .md", data=st.session_state.outputs[7],
                            file_name="stage_07_professor_brief.md", mime="text/markdown", key="dl_active_7")
                    if st.button("Continue to Stage 8 →", type="primary"):
                        st.session_state.stage = 8; st.rerun()
