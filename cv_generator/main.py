#!/usr/bin/env python3
"""
main.py
-------
Entry point for the ATS CV Generator.

Usage
-----
  # Launch GUI (default)
  python main.py

  # Launch CLI mode
  python main.py --mode cli

  # Show help
  python main.py --help
"""

import argparse
import os
import sys

# ── Ensure project root is on the path ──────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# ─────────────────────────────────────────────────────────────────────── #
#  CLI pipeline                                                            #
# ─────────────────────────────────────────────────────────────────────── #

def run_cli() -> None:
    """
    Run the application in interactive CLI mode.

    Pipeline:
      1. Collect user input          (InputCollector)
      2. Validate & clean data       (DataValidator)
      3. Normalise skill names       (SkillNormalizer)
      4. ATS keyword optimisation    (ATSOptimizer)
      5. Score ATS friendliness      (ATSScorer)
      6. Suggest improvements        (ImprovementSuggester)
      7. Generate PDF / DOCX / JSON  (PDFBuilder, DOCXBuilder, JSONBuilder)
    """
    from src.collector.input_collector          import InputCollector
    from src.processor.validator                import DataValidator
    from src.processor.normalizer               import SkillNormalizer
    from src.processor.optimizer                import ATSOptimizer
    from src.builder.pdf_builder                import PDFBuilder
    from src.builder.json_builder               import JSONBuilder
    from src.scorer.ats_scorer                  import ATSScorer
    from src.analyzer.improvement_suggester     import ImprovementSuggester

    print("\n" + "=" * 60)
    print("      ATS-FRIENDLY CV GENERATOR  (CLI Mode)")
    print("=" * 60)

    # ── Step 1: Collect ──────────────────────────────────────────────
    collector = InputCollector()
    cv_data   = collector.collect()

    # ── Step 2: Validate ─────────────────────────────────────────────
    print("\n[1/6] Validating input…")
    validator = DataValidator()
    cv_data   = validator.validate(cv_data)

    # ── Step 3: Normalise ────────────────────────────────────────────
    print("[2/6] Normalising skills…")
    normalizer = SkillNormalizer()
    cv_data    = normalizer.normalize(cv_data)

    # ── Step 4: Optimise ─────────────────────────────────────────────
    print("\n[3/6] ATS Keyword Optimisation")
    job_title = input(
        "  Enter target job title (e.g. 'Software Engineer'): "
    ).strip()
    job_desc_input = input(
        "  Paste job description for deeper matching? (y/n) [n]: "
    ).strip().lower()
    job_desc = None
    if job_desc_input in ("y", "yes"):
        print("  Paste job description (press Enter twice when done):")
        lines = []
        while True:
            line = input()
            if not line:
                break
            lines.append(line)
        job_desc = " ".join(lines) or None

    optimizer = ATSOptimizer()
    cv_data   = optimizer.optimize(cv_data, job_title, job_desc)

    # ── Step 5: Score ────────────────────────────────────────────────
    print("\n[4/6] Scoring ATS friendliness…")
    scorer       = ATSScorer()
    score_report = scorer.score(cv_data)

    print("\n" + "─" * 58)
    print(f"  ATS SCORE:  {score_report['total_score']}/100   "
          f"Grade: {score_report['grade']}")
    print("─" * 58)
    for dim, details in score_report["breakdown"].items():
        pts = details["score"]
        mx  = details["max"]
        bar = "█" * int(pts / mx * 16) + "░" * (16 - int(pts / mx * 16))
        print(f"  {dim:<26}  {pts:>2}/{mx}  [{bar}]")
        print(f"    ↳ {details['message']}")

    # ── Step 6: Suggest improvements ─────────────────────────────────
    print("\n[5/6] Analysing for improvements…")
    suggester   = ImprovementSuggester()
    suggestions = suggester.suggest(cv_data)

    if suggestions:
        print(f"\n  Found {len(suggestions)} suggestion(s):\n")
        for i, s in enumerate(suggestions, 1):
            priority = s.get("priority", "low").upper()
            print(f"  {i}. [{priority}]  {s['message']}\n")
    else:
        print("  No major issues found — your CV looks great!")

    # ── Step 7: Generate outputs ─────────────────────────────────────
    print("\n[6/6] Generating CV files…")
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    # PDF (always)
    pdf_builder = PDFBuilder()
    pdf_path    = pdf_builder.build(cv_data, output_dir)
    print(f"  ✓ PDF  → {os.path.abspath(pdf_path)}")

    # DOCX (optional, graceful fallback)
    try:
        from src.builder.docx_builder import DOCXBuilder
        docx_builder = DOCXBuilder()
        docx_path    = docx_builder.build(cv_data, output_dir)
        print(f"  ✓ DOCX → {os.path.abspath(docx_path)}")
    except ImportError:
        print("  ⚠ DOCX skipped (install python-docx: pip install python-docx)")

    # JSON (always)
    json_builder = JSONBuilder(output_dir)
    json_path    = json_builder.build(cv_data)
    print(f"  ✓ JSON → {os.path.abspath(json_path)}")

    print("\n" + "=" * 60)
    print("  CV generation complete!")
    print("=" * 60)


# ─────────────────────────────────────────────────────────────────────── #
#  GUI pipeline                                                            #
# ─────────────────────────────────────────────────────────────────────── #

def run_gui() -> None:
    """Launch the Tkinter GUI."""
    from src.gui.tkinter_gui import CVGeneratorGUI
    app = CVGeneratorGUI()
    app.run()


# ─────────────────────────────────────────────────────────────────────── #
#  Argument parsing & dispatch                                             #
# ─────────────────────────────────────────────────────────────────────── #

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="cv_generator",
        description="ATS-Friendly CV Generator — no LLMs required.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python main.py              # Launch GUI (default)\n"
            "  python main.py --mode cli   # Interactive CLI mode\n"
        ),
    )
    parser.add_argument(
        "--mode",
        choices=["gui", "cli"],
        default="gui",
        help="Run mode: 'gui' (default) opens the Tkinter window; "
             "'cli' uses the terminal.",
    )
    args = parser.parse_args()

    if args.mode == "cli":
        run_cli()
    else:
        run_gui()


if __name__ == "__main__":
    main()
