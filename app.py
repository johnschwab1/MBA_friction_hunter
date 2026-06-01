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
  Everything else stays the same.
"""

import io
import os
import re
from datetime import datetime
from pathlib import Path

import streamlit as st

# ── Load secrets into env before importing llm_client ──────────────────────
for _k in [
    "ANTHROPIC_API_KEY", "ANTHROPIC_MODEL",
    "GEMINI_API_KEY", "GEMINI_MODEL",
    "LLM_PROVIDER",
]:
    if _k in st.secrets:
        os.environ[_k] = st.secrets[_k]

from llm_client import call_llm, provider_label  # noqa: E402

# ── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MBA Friction Hunter",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Constants ───────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).parent

STAGE_NAMES = {
    2: "Friction Hunter",
    3: "Use Case Selector",
    4: "Architecture Hunter",
    5: "Design Brief",
    6: "Prototype",
}
STAGE_FILES = {
    2: "stage_2_friction_hunter.md",
    3: "stage_3_use_case_selector.md",
    4: "stage_4_architecture_hunter.md",
    5: "stage_5_design_brief_generator.md",
    6: "stage_6_prototype_generator.md",
}
STAGE_SLUGS = {
    2: "friction_hunter",
    3: "use_case_selector",
    4: "architecture_hunter",
    5: "design_brief",
    6: "prototype",
}
SEARCH_STAGES = {4}  # stages that use live web search

# ── Session state defaults ───────────────────────────────────────────────────
for _k, _v in {
    "syllabus": "",
    "outputs": {},
    "stage": 0,          # 0 = intake, 2–6 = pipeline
    "search_results": "",
    "search_fetched": False,
}.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


# ── Helpers ──────────────────────────────────────────────────────────────────

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
    return f.read().decode("utf-8", errors="replace")


def reset():
    for k in ["syllabus", "outputs", "stage", "search_results", "search_fetched"]:
        st.session_state[k] = {} if k == "outputs" else (False if k == "search_fetched" else "" if k != "stage" else 0)
    st.rerun()


# ── Header ───────────────────────────────────────────────────────────────────

col_title, col_badge = st.columns([5, 1])
with col_title:
    st.title("🎓 MBA Friction Hunter")
    st.caption("Find where AI creates genuine learning value in an MBA curriculum — then build a working prototype.")
with col_badge:
    st.markdown(f"<br><span style='font-size:0.8em;color:gray'>🤖 {provider_label()}</span>", unsafe_allow_html=True)

st.divider()


# ════════════════════════════════════════════════════════════════════════════
# INTAKE (stage == 0)
# ════════════════════════════════════════════════════════════════════════════

if st.session_state.stage == 0:
    st.subheader("Step 1 — Load the Syllabus")

    tab_search, tab_upload, tab_paste = st.tabs([
        "🔍  Search the web",
        "📁  Upload a file",
        "📝  Paste text",
    ])

    # ── Search tab ──
    with tab_search:
        st.caption("Search for a publicly available syllabus. You’ll see a list of options before we fetch the full text.")
        q_col, btn_col = st.columns([4, 1])
        with q_col:
            query = st.text_input(
                "Query", placeholder="e.g. Haas MBA marketing 2025",
                label_visibility="collapsed", key="search_query"
            )
        with btn_col:
            do_search = st.button("Search →", use_container_width=True)

        if do_search and query:
            with st.spinner(f"Searching for ‘{query}’…"):
                find_system = (
                    "You are a research assistant. Search for MBA course syllabi matching the user’s query. "
                    "Return a numbered list of up to 5 options. For each: number, title, school, year, "
                    "and one-sentence description. Format: N. Title — School (Year): Description"
                )
                st.session_state.search_results = call_llm(
                    find_system, f"Find MBA syllabi for: {query}",
                    use_search=True, max_tokens=800
                )
                st.session_state.search_fetched = False

        if st.session_state.search_results:
            st.markdown(st.session_state.search_results)
            st.divider()

            if not st.session_state.search_fetched:
                pick_col, fetch_col = st.columns([1, 3])
                with pick_col:
                    pick = st.number_input("Which result?", min_value=1, max_value=5, step=1)
                with fetch_col:
                    if st.button("Fetch full syllabus →", use_container_width=True):
                        with st.spinner("Fetching full syllabus…"):
                            fetch_system = (
                                "You are a research assistant. From the search results provided, fetch the full "
                                "text of the selected option. Return only the complete syllabus content: course "
                                "description, learning objectives, weekly schedule, assignments, and readings."
                            )
                            st.session_state.syllabus = call_llm(
                                fetch_system,
                                f"Results:\n\n{st.session_state.search_results}\n\nFetch full text of option {pick}.",
                                use_search=True, max_tokens=4096
                            )
                            st.session_state.search_fetched = True
                            st.rerun()
            else:
                st.success(f"✓ Fetched {len(st.session_state.syllabus):,} chars")
                with st.expander("Preview fetched syllabus"):
                    st.text(st.session_state.syllabus[:1000] + "…")
                if st.button("Start analysis →", type="primary", key="search_go"):
                    st.session_state.stage = 2
                    st.rerun()

    # ── Upload tab ──
    with tab_upload:
        st.caption("PDF, DOCX, and TXT supported.")
        uploaded = st.file_uploader(
            "File", type=["pdf", "docx", "txt"], label_visibility="collapsed"
        )
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

    # ── Paste tab ──
    with tab_paste:
        st.caption("Paste the syllabus text directly.")
        pasted = st.text_area(
            "Text", height=320,
            placeholder="Paste your syllabus here…",
            label_visibility="collapsed"
        )
        if st.button("Start analysis →", type="primary", key="paste_go") and pasted.strip():
            st.session_state.syllabus = pasted.strip()
            st.session_state.stage = 2
            st.rerun()


# ════════════════════════════════════════════════════════════════════════════
# PIPELINE (stage 2–6)
# ════════════════════════════════════════════════════════════════════════════

elif st.session_state.stage >= 2:
    criteria = load_criteria()

    # Restart button
    if st.button("↩ New syllabus"):
        reset()

    # ── Completed stages (collapsed) ──
    for s in range(2, st.session_state.stage):
        if s in st.session_state.outputs:
            with st.expander(f"✅ Stage {s}: {STAGE_NAMES[s]}", expanded=False):
                st.markdown(st.session_state.outputs[s])
                dl_col, _ = st.columns([1, 3])
                with dl_col:
                    st.download_button(
                        label="Download .md",
                        data=st.session_state.outputs[s],
                        file_name=f"stage_{s:02d}_{STAGE_SLUGS[s]}.md",
                        mime="text/markdown",
                        key=f"dl_done_{s}",
                    )

    active = st.session_state.stage

    if active <= 6:
        st.subheader(f"Stage {active}: {STAGE_NAMES[active]}")
        if active == 4:
            st.caption("🔍 Web search active — finding current research and frameworks")

        # ── Stage not yet run ──
        if active not in st.session_state.outputs:
            if st.button(f"Run Stage {active} →", type="primary"):
                system = extract_system_prompt(STAGE_FILES[active])

                if active == 2:
                    user_msg = (
                        f"CRITERIA REFERENCE:\n\n{criteria}\n\n---\n\n"
                        f"CURRICULUM TO ANALYZE:\n\n{st.session_state.syllabus}"
                    )
                elif active == 5 and 3 in st.session_state.outputs and 4 in st.session_state.outputs:
                    user_msg = (
                        f"PRIORITIZED USE CASES (Stage 3):\n\n{st.session_state.outputs[3]}\n\n---\n\n"
                        f"ARCHITECTURE RECOMMENDATIONS (Stage 4):\n\n{st.session_state.outputs[4]}"
                    )
                else:
                    user_msg = st.session_state.outputs.get(active - 1, st.session_state.syllabus)

                with st.spinner(f"{STAGE_NAMES[active]}…"):
                    result = call_llm(
                        system, user_msg,
                        use_search=(active in SEARCH_STAGES)
                    )
                st.session_state.outputs[active] = result
                st.rerun()

        # ── Stage complete ──
        else:
            st.markdown(st.session_state.outputs[active])
            st.divider()

            action_col, dl_col, _ = st.columns([2, 2, 3])
            with action_col:
                if st.button("↺ Re-run this stage"):
                    del st.session_state.outputs[active]
                    st.rerun()
            with dl_col:
                st.download_button(
                    label="Download .md",
                    data=st.session_state.outputs[active],
                    file_name=f"stage_{active:02d}_{STAGE_SLUGS[active]}.md",
                    mime="text/markdown",
                    key=f"dl_active_{active}",
                )

            if active < 6:
                if st.button(f"Continue to Stage {active + 1} →", type="primary"):
                    st.session_state.stage += 1
                    st.rerun()
            else:
                st.success("🏁 Pipeline complete!")
                st.subheader("Download all outputs")
                for s in range(2, 7):
                    if s in st.session_state.outputs:
                        st.download_button(
                            label=f"Stage {s}: {STAGE_NAMES[s]}",
                            data=st.session_state.outputs[s],
                            file_name=f"stage_{s:02d}_{STAGE_SLUGS[s]}.md",
                            mime="text/markdown",
                            key=f"dl_final_{s}",
                        )
