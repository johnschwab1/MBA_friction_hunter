#!/usr/bin/env python3
"""
MBA Friction Hunter — Pipeline Runner

Chains all 6 stages of the friction hunting workflow using the Anthropic API.
Web search is enabled at Stage 4 (Architecture Hunter) so it actively finds
current research, not just training data. The --search flag lets you find a
syllabus by query rather than pasting one.

Usage:
  python run_pipeline.py --search "Haas MBA marketing syllabus 2025"
  python run_pipeline.py --input syllabus.txt
  python run_pipeline.py --input syllabus.txt --from-stage 4
  python run_pipeline.py --input syllabus.txt --auto
  python run_pipeline.py --input syllabus.txt --name haas_marketing

Outputs are saved to output/<run_name>/stage_NN_<name>.md
You can edit any stage output before continuing to the next stage.

Requires:
  ANTHROPIC_API_KEY environment variable (or .env file)
  pip install anthropic python-dotenv
"""

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

try:
    import anthropic
except ImportError:
    sys.exit("Missing dependency: pip install anthropic")

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # .env support is optional

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_MODEL = "claude-opus-4-8"  # Best analytical quality for pipeline work

STAGE_FILES = {
    2: "stage_2_friction_hunter.md",
    3: "stage_3_use_case_selector.md",
    4: "stage_4_architecture_hunter.md",
    5: "stage_5_design_brief_generator.md",
    6: "stage_6_prototype_generator.md",
}

STAGE_NAMES = {
    2: "friction_hunter",
    3: "use_case_selector",
    4: "architecture_hunter",
    5: "design_brief",
    6: "prototype",
}

# Stage 4 uses live web search to find current research, not just training data.
# You can extend this set if you want search at other stages too.
SEARCH_STAGES = {4}


# ---------------------------------------------------------------------------
# Core API call — handles tool-use loop for web search
# ---------------------------------------------------------------------------

def call_claude(
    client: "anthropic.Anthropic",
    system: str,
    user: str,
    use_search: bool = False,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 8192,
) -> str:
    """
    Call Claude and return the final text response.

    Handles the tool-use loop so web search calls resolve automatically.
    Anthropic's web_search_20250305 tool is server-side: the API executes
    searches and returns results; we just need to keep the loop going until
    stop_reason is 'end_turn'.
    """
    tools = []
    if use_search:
        tools = [{"type": "web_search_20250305", "name": "web_search", "max_uses": 5}]

    messages = [{"role": "user", "content": user}]

    for _ in range(20):  # safety cap on tool-use iterations
        kwargs: dict = {
            "model": model,
            "max_tokens": max_tokens,
            "system": system,
            "messages": messages,
        }
        if tools:
            kwargs["tools"] = tools

        response = client.messages.create(**kwargs)

        # Collect text blocks and any tool-use blocks from this turn
        text_parts: list[str] = []
        tool_uses: list = []
        for block in response.content:
            if hasattr(block, "text"):
                text_parts.append(block.text)
            if getattr(block, "type", "") == "tool_use":
                tool_uses.append(block)

        if response.stop_reason == "end_turn" or not tool_uses:
            return "\n".join(text_parts)

        # Tool-use loop: append this assistant turn, then return empty tool results.
        # For web_search_20250305, Anthropic populates results server-side;
        # sending an empty content string is the correct acknowledgement.
        messages.append({"role": "assistant", "content": response.content})
        tool_results = [
            {"type": "tool_result", "tool_use_id": tu.id, "content": ""}
            for tu in tool_uses
        ]
        messages.append({"role": "user", "content": tool_results})

    return "\n".join(text_parts)  # fallback if cap hit


# ---------------------------------------------------------------------------
# Stage helpers
# ---------------------------------------------------------------------------

def extract_system_prompt(md_path: Path) -> str:
    """Pull everything after '## System Prompt' from a stage markdown file."""
    text = md_path.read_text()
    match = re.search(r"## System Prompt\s*\n(.*)", text, re.DOTALL)
    if not match:
        raise ValueError(f"No '## System Prompt' section found in {md_path}")
    return match.group(1).strip()


def save_stage(output_dir: Path, stage_num: int, content: str) -> Path:
    name = STAGE_NAMES[stage_num]
    path = output_dir / f"stage_{stage_num:02d}_{name}.md"
    path.write_text(content)
    return path


def pause_and_preview(stage_num: int, path: Path) -> bool:
    """Show a preview of stage output and ask whether to continue."""
    content = path.read_text()
    label = STAGE_NAMES[stage_num].replace("_", " ").title()
    sep = "─" * 60
    print(f"\n{sep}")
    print(f"✓ Stage {stage_num}: {label}  →  {path}")
    print(sep)
    preview = content[:900] + ("…" if len(content) > 900 else "")
    print(preview)
    print()
    ans = input("Continue to next stage? [Y/n/e(dit)]: ").strip().lower()
    if ans in ("e", "edit"):
        # Let the user edit the output file before continuing
        import os, subprocess
        editor = os.environ.get("EDITOR", "nano")
        subprocess.call([editor, str(path)])
        print(f"  Reloaded edited output from {path}")
        return True
    return ans not in ("n", "no", "q", "quit")


# ---------------------------------------------------------------------------
# Syllabus fetcher (--search mode)
# ---------------------------------------------------------------------------

def fetch_syllabus(client: "anthropic.Anthropic", query: str, model: str) -> str:
    """
    Use web search to find a syllabus and return its full text.
    Designed to find publicly available course syllabi by name or description.
    """
    print(f"  Searching for: {query}")
    system = (
        "You are a research assistant. The user wants to find an MBA or business school "
        "course syllabus. Search for it, find the most recent publicly available version, "
        "and return the complete syllabus text including: course description, learning "
        "objectives, weekly schedule, assignments, and required readings. "
        "Return only the syllabus content itself, not commentary about it."
    )
    user = f"Find and return the complete text of this syllabus: {query}"
    return call_claude(client, system, user, use_search=True, model=model, max_tokens=4096)


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def run_pipeline(args: argparse.Namespace) -> None:
    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env

    run_name = args.name or datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path("output") / run_name
    output_dir.mkdir(parents=True, exist_ok=True)

    repo_root = Path(__file__).parent

    print(f"\nMBA Friction Hunter Pipeline")
    print(f"Model: {args.model}")
    print(f"Output: {output_dir}\n")

    # --- Step 0: Get the syllabus ---
    if args.search:
        print("Stage 0: Fetching syllabus via web search...")
        syllabus = fetch_syllabus(client, args.search, args.model)
        syl_path = output_dir / "stage_00_syllabus.md"
        syl_path.write_text(syllabus)
        print(f"  Fetched {len(syllabus):,} chars  →  {syl_path}")
        if not args.auto:
            input("  Review the fetched syllabus, then press Enter to continue...")
    elif args.input:
        syllabus = Path(args.input).read_text()
        print(f"Loaded syllabus from {args.input} ({len(syllabus):,} chars)")
    else:
        print("Paste curriculum text, then press Ctrl+D (Ctrl+Z on Windows):")
        syllabus = sys.stdin.read()
        print(f"  Read {len(syllabus):,} chars from stdin")

    # Criteria document is injected into Stage 2 as a reference
    criteria_text = (repo_root / "stage_1_criteria_layer.md").read_text()

    # Track outputs keyed by stage number for cross-stage injection
    outputs: dict[int, str] = {}

    # --- If resuming from a later stage, load prior outputs ---
    if args.from_stage > 2:
        for s in range(2, args.from_stage):
            candidate = output_dir / f"stage_{s:02d}_{STAGE_NAMES[s]}.md"
            if candidate.exists():
                outputs[s] = candidate.read_text()
                print(f"  Loaded prior Stage {s} output from {candidate}")
            else:
                print(f"  Warning: no saved output for Stage {s}; will use raw syllabus as fallback")

    current_text = syllabus

    # --- Run each stage ---
    for stage_num in range(args.from_stage, 7):
        md_file = repo_root / STAGE_FILES[stage_num]
        system_prompt = extract_system_prompt(md_file)
        use_search = stage_num in SEARCH_STAGES

        # Build the user message with appropriate context injection
        if stage_num == 2:
            user_msg = (
                "CRITERIA REFERENCE (use to calibrate your scoring):\n\n"
                f"{criteria_text}\n\n---\n\n"
                f"CURRICULUM TO ANALYZE:\n\n{current_text}"
            )
        elif stage_num == 5 and 3 in outputs and 4 in outputs:
            # Design Brief needs both use cases (Stage 3) and architectures (Stage 4)
            user_msg = (
                "PRIORITIZED USE CASES (Stage 3 output):\n\n"
                f"{outputs[3]}\n\n---\n\n"
                "ARCHITECTURE RECOMMENDATIONS (Stage 4 output):\n\n"
                f"{outputs[4]}"
            )
        else:
            user_msg = current_text

        label = STAGE_NAMES[stage_num].replace("_", " ").title()
        search_note = " [web search active]" if use_search else ""
        print(f"\nStage {stage_num}: {label}{search_note}...")

        result = call_claude(
            client, system_prompt, user_msg,
            use_search=use_search, model=args.model
        )

        outputs[stage_num] = result
        path = save_stage(output_dir, stage_num, result)
        current_text = result

        if stage_num < 6 and not args.auto:
            if not pause_and_preview(stage_num, path):
                print(f"\nPaused after Stage {stage_num}. All outputs in: {output_dir}")
                sys.exit(0)
        else:
            print(f"  ✓ {path}")

    print(f"\nPipeline complete. All outputs in: {output_dir}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="MBA Friction Hunter — chains all 6 analysis stages",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    src = parser.add_mutually_exclusive_group()
    src.add_argument(
        "--input", "-i", metavar="FILE",
        help="Path to a syllabus text or PDF text file"
    )
    src.add_argument(
        "--search", "-s", metavar="QUERY",
        help="Find a syllabus by search query, e.g. 'Haas MBA marketing syllabus 2025'"
    )

    parser.add_argument(
        "--from-stage", type=int, default=2, choices=[2, 3, 4, 5, 6],
        metavar="N",
        help="Resume from stage N (2–6). Looks for prior stage outputs in the output folder."
    )
    parser.add_argument(
        "--name", "-n", metavar="NAME",
        help="Name for this run's output folder (default: timestamp)"
    )
    parser.add_argument(
        "--auto", "-a", action="store_true",
        help="Run all stages without pause/confirmation prompts"
    )
    parser.add_argument(
        "--model", default=DEFAULT_MODEL,
        help=f"Anthropic model to use (default: {DEFAULT_MODEL})"
    )

    args = parser.parse_args()
    run_pipeline(args)


if __name__ == "__main__":
    main()
