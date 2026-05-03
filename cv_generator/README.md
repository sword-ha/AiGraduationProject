# ATS CV Generator

A complete, production-quality Python project that generates ATS-optimised CVs
in **PDF**, **DOCX**, and **JSON** formats — with zero LLMs or external AI APIs.

---

## Features

| Feature | Details |
|---|---|
| **Data collection** | Interactive CLI wizard *or* full Tkinter GUI |
| **Validation** | Email/phone/URL format checks, required-field warnings |
| **Skill normalisation** | 80+ aliases mapped (`js` → `JavaScript`, `k8s` → `Kubernetes`) |
| **ATS optimisation** | TF-IDF keyword matching against 10 job-title profiles |
| **ATS scoring** | 6-dimensional, 100-point rubric with letter grade |
| **Improvement suggestions** | 12 rule-based checks (weak verbs, metrics, duplicates…) |
| **PDF export** | ReportLab Platypus, ATS-safe single-column layout |
| **DOCX export** | python-docx with built-in Word styles |
| **JSON export** | Versioned save/load with metadata |
| **Multi-version support** | Name, label and timestamp multiple saved CVs |

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Launch GUI (default)
python main.py

# 3. Or use the CLI
python main.py --mode cli
```

---

## Project Structure

```
cv_generator/
├── main.py                              # Entry point (CLI + GUI)
├── requirements.txt
├── data/
│   ├── keywords.json                    # Job-title keyword profiles + alias map
│   └── example_cv.json                  # Sample CV for testing
├── output/                              # Generated files saved here
└── src/
    ├── collector/
    │   └── input_collector.py           # CLI interview wizard
    ├── processor/
    │   ├── validator.py                 # Input validation & cleaning
    │   ├── normalizer.py                # Skill name normalisation
    │   └── optimizer.py                 # TF-IDF keyword optimisation
    ├── builder/
    │   ├── pdf_builder.py               # ReportLab PDF generation
    │   ├── docx_builder.py              # python-docx DOCX generation
    │   └── json_builder.py              # JSON export + version management
    ├── scorer/
    │   └── ats_scorer.py                # 6-dimensional ATS scoring (0-100)
    ├── analyzer/
    │   └── improvement_suggester.py     # 12 rule-based improvement checks
    └── gui/
        └── tkinter_gui.py               # Full Tkinter GUI (6 tabs)
```

---

## Architecture

```
User Input
    │
    ▼
InputCollector  ──────────────────────────────────── CLI or GUI
    │
    ▼
DataValidator   ── email / phone / URL checks, field cleaning
    │
    ▼
SkillNormalizer ── alias resolution  (js → JavaScript)
    │
    ▼
ATSOptimizer    ── TF-IDF keyword matching vs. job title profile
    │
    ├──▶ ATSScorer            ── 100-point score + letter grade
    │
    ├──▶ ImprovementSuggester ── 12 rule-based checks
    │
    └──▶ Builders
              PDFBuilder  ── ReportLab ATS-safe PDF
              DOCXBuilder ── python-docx DOCX
              JSONBuilder ── versioned JSON export
```

---

## ATS Scoring Dimensions

| Dimension | Max | What it checks |
|---|---|---|
| Section Completeness | 30 | Name, summary, experience, education, skills, projects |
| Keyword Coverage | 25 | % of target job-title keywords present |
| Action Verb Quality | 15 | Strong action verbs at start of bullets |
| Quantification | 15 | Numbers / metrics in experience bullets |
| Formatting Quality | 10 | Summary length, bullet count, special chars |
| Contact Completeness | 5 | Name, email, phone all present |

Grade scale: **A+ ≥ 90 · A ≥ 80 · B ≥ 70 · C ≥ 60 · D ≥ 50 · F < 50**

---

## Dependencies

| Package | Purpose |
|---|---|
| `reportlab` | PDF generation |
| `python-docx` | DOCX generation *(optional)* |
| `colorama` | Coloured CLI output *(optional)* |

All standard library — no OpenAI, no HuggingFace, no ML frameworks.

---

## Example Output

Running the example CV produces:

```
ATS Score: 82/100   Grade: A
  Section Completeness  : 30/30
  Keyword Coverage      : 20/25   (38% of 45 keywords matched)
  Action Verb Quality   : 15/15
  Quantification        : 15/15
  Formatting Quality    :  7/10
  Contact Completeness  :  5/5
```

---

## GUI Tabs

1. **Personal** — name, contact, summary
2. **Education** — multiple entries, add/remove
3. **Experience** — multiple roles with bullet points
4. **Skills** — technical / soft / tools (comma-separated)
5. **Projects** — name, description, technologies, link
6. **Generate ★** — ATS score display, export buttons, version management
