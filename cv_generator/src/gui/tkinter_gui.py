"""
tkinter_gui.py
--------------
Full Tkinter-based GUI for the ATS CV Generator.

Layout
------
  Root Window
  ├── Menu bar  (File → Save JSON / Load Version / Exit)
  ├── ttk.Notebook  (6 tabs)
  │   ├── Tab 1: Personal Info
  │   ├── Tab 2: Education       (dynamic add/remove entries)
  │   ├── Tab 3: Experience      (dynamic add/remove entries)
  │   ├── Tab 4: Skills
  │   ├── Tab 5: Projects        (dynamic add/remove entries)
  │   └── Tab 6: Generate & Score
  └── Status bar

All long-running operations (PDF generation, scoring) run in a
background thread so the GUI stays responsive.
"""

import json
import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
from typing import Any, Dict, List, Optional

# ── Project root on the path so src.* imports work ──────────────────────
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from src.processor.validator          import DataValidator
from src.processor.normalizer         import SkillNormalizer
from src.processor.optimizer          import ATSOptimizer
from src.builder.pdf_builder          import PDFBuilder
from src.builder.json_builder         import JSONBuilder
from src.scorer.ats_scorer            import ATSScorer
from src.analyzer.improvement_suggester import ImprovementSuggester


# ─────────────────────────────────────────────────────────────────────── #
#  Colour / style palette                                                  #
# ─────────────────────────────────────────────────────────────────────── #
PALETTE = {
    "bg":        "#f5f5f5",
    "sidebar":   "#1a1a2e",
    "accent":    "#e94560",
    "btn_bg":    "#16213e",
    "btn_fg":    "#ffffff",
    "heading":   "#1a1a2e",
    "label":     "#333333",
    "entry_bg":  "#ffffff",
    "score_a":   "#27ae60",
    "score_b":   "#f39c12",
    "score_c":   "#e74c3c",
    "tab_bg":    "#eef0f5",
}

FONT_NORMAL = ("Segoe UI", 10)
FONT_BOLD   = ("Segoe UI", 10, "bold")
FONT_LARGE  = ("Segoe UI", 14, "bold")
FONT_MONO   = ("Consolas",  9)


# ─────────────────────────────────────────────────────────────────────── #
#  Helper widgets                                                          #
# ─────────────────────────────────────────────────────────────────────── #

class LabeledEntry(tk.Frame):
    """A Label + Entry pair stacked vertically."""

    def __init__(
        self,
        parent,
        label: str,
        placeholder: str = "",
        width: int = 40,
        **kwargs,
    ) -> None:
        super().__init__(parent, bg=PALETTE["bg"], **kwargs)
        tk.Label(
            self, text=label, font=FONT_BOLD,
            bg=PALETTE["bg"], fg=PALETTE["label"], anchor="w",
        ).pack(fill="x")
        self.var = tk.StringVar()
        self._entry = tk.Entry(
            self, textvariable=self.var,
            font=FONT_NORMAL, width=width,
            bg=PALETTE["entry_bg"], relief="solid", bd=1,
        )
        self._entry.pack(fill="x", pady=(2, 6))
        if placeholder:
            self._set_placeholder(placeholder)

    def _set_placeholder(self, text: str) -> None:
        self._entry.insert(0, text)
        self._entry.config(fg="#aaaaaa")

        def on_focus_in(e):
            if self._entry.cget("fg") == "#aaaaaa":
                self._entry.delete(0, "end")
                self._entry.config(fg="#000000")

        def on_focus_out(e):
            if not self._entry.get():
                self._entry.insert(0, text)
                self._entry.config(fg="#aaaaaa")

        self._entry.bind("<FocusIn>",  on_focus_in)
        self._entry.bind("<FocusOut>", on_focus_out)

    def get(self) -> str:
        val = self.var.get().strip()
        # Ignore placeholder text
        if self._entry.cget("fg") == "#aaaaaa":
            return ""
        return val

    def set(self, value: str) -> None:
        self._entry.config(fg="#000000")
        self.var.set(value)


class LabeledTextArea(tk.Frame):
    """A Label + ScrolledText pair stacked vertically."""

    def __init__(
        self,
        parent,
        label: str,
        height: int = 4,
        width: int = 50,
        **kwargs,
    ) -> None:
        super().__init__(parent, bg=PALETTE["bg"], **kwargs)
        tk.Label(
            self, text=label, font=FONT_BOLD,
            bg=PALETTE["bg"], fg=PALETTE["label"], anchor="w",
        ).pack(fill="x")
        self._text = scrolledtext.ScrolledText(
            self, height=height, width=width,
            font=FONT_NORMAL, bg=PALETTE["entry_bg"],
            relief="solid", bd=1, wrap=tk.WORD,
        )
        self._text.pack(fill="both", expand=True, pady=(2, 6))

    def get(self) -> str:
        return self._text.get("1.0", tk.END).strip()

    def set(self, value: str) -> None:
        self._text.delete("1.0", tk.END)
        self._text.insert("1.0", value)


def _make_button(parent, text: str, command, **kwargs) -> tk.Button:
    """Create a consistently styled button."""
    return tk.Button(
        parent, text=text, command=command,
        font=FONT_BOLD,
        bg=kwargs.pop("bg", PALETTE["btn_bg"]),
        fg=kwargs.pop("fg", PALETTE["btn_fg"]),
        relief="flat", padx=12, pady=6,
        cursor="hand2", activebackground=PALETTE["accent"],
        activeforeground="#ffffff", **kwargs,
    )


# ─────────────────────────────────────────────────────────────────────── #
#  Dynamic list panel (Education / Experience / Projects)                 #
# ─────────────────────────────────────────────────────────────────────── #

class EntryPanel(tk.Frame):
    """
    A scrollable panel that holds N instances of a given entry widget.
    Users can add and remove entries dynamically.
    """

    def __init__(self, parent, entry_class, entry_kwargs=None, **kwargs) -> None:
        super().__init__(parent, bg=PALETTE["bg"], **kwargs)
        self._entry_class  = entry_class
        self._entry_kwargs = entry_kwargs or {}
        self._entries: List[Any] = []

        # Toolbar
        toolbar = tk.Frame(self, bg=PALETTE["bg"])
        toolbar.pack(fill="x", pady=(0, 6))
        _make_button(toolbar, "+ Add Entry", self._add_entry).pack(side="left", padx=4)
        _make_button(
            toolbar, "- Remove Last", self._remove_last,
            bg="#c0392b",
        ).pack(side="left", padx=4)

        # Scrollable canvas
        canvas = tk.Canvas(self, bg=PALETTE["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self._scroll_frame = tk.Frame(canvas, bg=PALETTE["bg"])

        self._scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.create_window((0, 0), window=self._scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        # Start with one empty entry
        self._add_entry()

    def _add_entry(self) -> None:
        entry = self._entry_class(self._scroll_frame, **self._entry_kwargs)
        entry.pack(fill="x", padx=8, pady=4)
        self._entries.append(entry)

    def _remove_last(self) -> None:
        if len(self._entries) > 1:
            widget = self._entries.pop()
            widget.destroy()

    def get_all(self) -> List[Dict[str, Any]]:
        """Return a list of dicts, one per entry widget."""
        return [e.get_data() for e in self._entries]

    def set_all(self, data_list: List[Dict[str, Any]]) -> None:
        """Populate entries from a list of dicts."""
        # Remove all current entries
        for entry in self._entries:
            entry.destroy()
        self._entries.clear()
        # Create new entries
        for data in data_list:
            entry = self._entry_class(self._scroll_frame, **self._entry_kwargs)
            entry.pack(fill="x", padx=8, pady=4)
            entry.set_data(data)
            self._entries.append(entry)
        if not self._entries:
            self._add_entry()


# ─────────────────────────────────────────────────────────────────────── #
#  Individual entry widgets                                                #
# ─────────────────────────────────────────────────────────────────────── #

class EducationEntry(tk.LabelFrame):
    def __init__(self, parent, **kwargs) -> None:
        super().__init__(
            parent, text="Education Entry",
            font=FONT_BOLD, bg=PALETTE["bg"], fg=PALETTE["heading"],
            relief="groove", bd=1, padx=8, pady=6, **kwargs,
        )
        self._institution = LabeledEntry(self, "Institution *", "e.g. Massachusetts Institute of Technology")
        self._institution.pack(fill="x")
        self._degree = LabeledEntry(self, "Degree", "e.g. Bachelor of Science")
        self._degree.pack(fill="x")
        self._field = LabeledEntry(self, "Field of Study", "e.g. Computer Science")
        self._field.pack(fill="x")

        row = tk.Frame(self, bg=PALETTE["bg"])
        row.pack(fill="x")
        self._start = LabeledEntry(row, "Start Date", "e.g. Sep 2018", width=18)
        self._start.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self._end = LabeledEntry(row, "End Date", "e.g. Jun 2022 or Present", width=18)
        self._end.pack(side="left", fill="x", expand=True)

        self._gpa = LabeledEntry(self, "GPA (optional)", "e.g. 3.8 / 4.0")
        self._gpa.pack(fill="x")
        self._achievements = LabeledTextArea(self, "Achievements / Activities (one per line)", height=3)
        self._achievements.pack(fill="x")

    def get_data(self) -> Dict[str, Any]:
        raw_ach = self._achievements.get()
        achievements = [a.strip() for a in raw_ach.splitlines() if a.strip()]
        return {
            "institution":  self._institution.get(),
            "degree":       self._degree.get(),
            "field":        self._field.get(),
            "start_date":   self._start.get(),
            "end_date":     self._end.get(),
            "gpa":          self._gpa.get(),
            "achievements": achievements,
        }

    def set_data(self, data: Dict[str, Any]) -> None:
        self._institution.set(data.get("institution", ""))
        self._degree.set(data.get("degree", ""))
        self._field.set(data.get("field", ""))
        self._start.set(data.get("start_date", ""))
        self._end.set(data.get("end_date", ""))
        self._gpa.set(data.get("gpa", ""))
        self._achievements.set("\n".join(data.get("achievements", [])))


class ExperienceEntry(tk.LabelFrame):
    def __init__(self, parent, **kwargs) -> None:
        super().__init__(
            parent, text="Experience Entry",
            font=FONT_BOLD, bg=PALETTE["bg"], fg=PALETTE["heading"],
            relief="groove", bd=1, padx=8, pady=6, **kwargs,
        )
        row1 = tk.Frame(self, bg=PALETTE["bg"])
        row1.pack(fill="x")
        self._company = LabeledEntry(row1, "Company *", "e.g. Google", width=28)
        self._company.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self._title = LabeledEntry(row1, "Job Title *", "e.g. Software Engineer", width=28)
        self._title.pack(side="left", fill="x", expand=True)

        row2 = tk.Frame(self, bg=PALETTE["bg"])
        row2.pack(fill="x")
        self._start = LabeledEntry(row2, "Start Date", "e.g. Jul 2022", width=18)
        self._start.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self._end = LabeledEntry(row2, "End Date", "e.g. Present", width=18)
        self._end.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self._location = LabeledEntry(row2, "Location", "e.g. New York, NY", width=24)
        self._location.pack(side="left", fill="x", expand=True)

        self._bullets = LabeledTextArea(
            self,
            "Key Achievements / Responsibilities\n"
            "  (one bullet per line, start with a strong action verb)",
            height=5,
        )
        self._bullets.pack(fill="x")

    def get_data(self) -> Dict[str, Any]:
        raw = self._bullets.get()
        bullets = [b.strip().lstrip("-•* ") for b in raw.splitlines() if b.strip()]
        return {
            "company":    self._company.get(),
            "title":      self._title.get(),
            "start_date": self._start.get(),
            "end_date":   self._end.get(),
            "location":   self._location.get(),
            "bullets":    bullets,
        }

    def set_data(self, data: Dict[str, Any]) -> None:
        self._company.set(data.get("company", ""))
        self._title.set(data.get("title", ""))
        self._start.set(data.get("start_date", ""))
        self._end.set(data.get("end_date", ""))
        self._location.set(data.get("location", ""))
        self._bullets.set("\n".join(data.get("bullets", [])))


class ProjectEntry(tk.LabelFrame):
    def __init__(self, parent, **kwargs) -> None:
        super().__init__(
            parent, text="Project Entry",
            font=FONT_BOLD, bg=PALETTE["bg"], fg=PALETTE["heading"],
            relief="groove", bd=1, padx=8, pady=6, **kwargs,
        )
        self._name = LabeledEntry(self, "Project Name *", "e.g. Real-Time Analytics Dashboard")
        self._name.pack(fill="x")
        self._description = LabeledTextArea(
            self, "Description (what it does, your role, impact)", height=3
        )
        self._description.pack(fill="x")
        self._technologies = LabeledEntry(
            self, "Technologies (comma-separated)", "e.g. Python, React, PostgreSQL, Docker"
        )
        self._technologies.pack(fill="x")
        self._link = LabeledEntry(self, "Link (GitHub / Live URL)", "e.g. github.com/user/repo")
        self._link.pack(fill="x")

    def get_data(self) -> Dict[str, Any]:
        raw_tech = self._technologies.get()
        technologies = [t.strip() for t in raw_tech.split(",") if t.strip()]
        return {
            "name":         self._name.get(),
            "description":  self._description.get(),
            "technologies": technologies,
            "link":         self._link.get(),
        }

    def set_data(self, data: Dict[str, Any]) -> None:
        self._name.set(data.get("name", ""))
        self._description.set(data.get("description", ""))
        self._technologies.set(", ".join(data.get("technologies", [])))
        self._link.set(data.get("link", ""))


# ─────────────────────────────────────────────────────────────────────── #
#  Main Application                                                        #
# ─────────────────────────────────────────────────────────────────────── #

class CVGeneratorGUI:
    """
    Root application window.

    Manages state, coordinates tabs, and calls backend modules on demand.
    """

    def __init__(self) -> None:
        self._root = tk.Tk()
        self._root.title("ATS CV Generator")
        self._root.geometry("920x700")
        self._root.minsize(800, 600)
        self._root.configure(bg=PALETTE["bg"])

        self._output_dir = "output"
        os.makedirs(self._output_dir, exist_ok=True)

        self._json_builder = JSONBuilder(self._output_dir)
        self._last_cv_data: Optional[Dict[str, Any]] = None

        self._build_menu()
        self._build_notebook()
        self._build_status_bar()

    # ------------------------------------------------------------------ #
    #  Menu                                                                #
    # ------------------------------------------------------------------ #

    def _build_menu(self) -> None:
        menubar = tk.Menu(self._root)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Load Saved Version…", command=self._load_version)
        file_menu.add_command(label="Save as JSON",        command=self._save_json)
        file_menu.add_separator()
        file_menu.add_command(label="Exit",                command=self._root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About",               command=self._show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        self._root.config(menu=menubar)

    # ------------------------------------------------------------------ #
    #  Notebook tabs                                                       #
    # ------------------------------------------------------------------ #

    def _build_notebook(self) -> None:
        style = ttk.Style()
        style.configure("TNotebook",       background=PALETTE["bg"])
        style.configure("TNotebook.Tab",   font=FONT_BOLD, padding=[10, 5])
        style.configure("TFrame",          background=PALETTE["bg"])

        self._notebook = ttk.Notebook(self._root)
        self._notebook.pack(fill="both", expand=True, padx=10, pady=(10, 4))

        self._tab_personal    = self._build_tab_personal()
        self._tab_education   = self._build_tab_education()
        self._tab_experience  = self._build_tab_experience()
        self._tab_skills      = self._build_tab_skills()
        self._tab_projects    = self._build_tab_projects()
        self._tab_generate    = self._build_tab_generate()

        self._notebook.add(self._tab_personal,   text="  Personal  ")
        self._notebook.add(self._tab_education,  text=" Education  ")
        self._notebook.add(self._tab_experience, text=" Experience ")
        self._notebook.add(self._tab_skills,     text="   Skills   ")
        self._notebook.add(self._tab_projects,   text="  Projects  ")
        self._notebook.add(self._tab_generate,   text=" Generate ★ ")

    # ── Tab 1: Personal ─────────────────────────────────────────────── #

    def _build_tab_personal(self) -> ttk.Frame:
        frame = ttk.Frame(self._notebook)
        canvas = tk.Canvas(frame, bg=PALETTE["bg"], highlightthickness=0)
        sb = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg=PALETTE["bg"])
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        pad = {"padx": 16, "pady": 4}

        tk.Label(inner, text="Personal Information", font=FONT_LARGE,
                 bg=PALETTE["bg"], fg=PALETTE["heading"]).pack(anchor="w", **pad)
        ttk.Separator(inner, orient="horizontal").pack(fill="x", padx=16, pady=2)

        self._name     = LabeledEntry(inner, "Full Name *",      "e.g. Jane Smith")
        self._name.pack(fill="x", **pad)
        self._email    = LabeledEntry(inner, "Email Address *",  "e.g. jane@example.com")
        self._email.pack(fill="x", **pad)
        self._phone    = LabeledEntry(inner, "Phone Number *",   "e.g. +1 (555) 123-4567")
        self._phone.pack(fill="x", **pad)

        row = tk.Frame(inner, bg=PALETTE["bg"])
        row.pack(fill="x", **pad)
        self._linkedin = LabeledEntry(row, "LinkedIn URL",       "linkedin.com/in/janesmit", width=36)
        self._linkedin.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self._github   = LabeledEntry(row, "GitHub URL",         "github.com/janesmith", width=36)
        self._github.pack(side="left", fill="x", expand=True)

        row2 = tk.Frame(inner, bg=PALETTE["bg"])
        row2.pack(fill="x", **pad)
        self._location = LabeledEntry(row2, "Location",          "e.g. New York, NY", width=36)
        self._location.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self._website  = LabeledEntry(row2, "Personal Website",  "e.g. janesmith.dev", width=36)
        self._website.pack(side="left", fill="x", expand=True)

        self._summary  = LabeledTextArea(
            inner,
            "Professional Summary  (40-80 words recommended)",
            height=6,
        )
        self._summary.pack(fill="x", **pad)

        return frame

    # ── Tab 2: Education ────────────────────────────────────────────── #

    def _build_tab_education(self) -> ttk.Frame:
        frame = ttk.Frame(self._notebook)
        tk.Label(frame, text="Education History", font=FONT_LARGE,
                 bg=PALETTE["bg"], fg=PALETTE["heading"]).pack(anchor="w", padx=16, pady=(8, 4))
        ttk.Separator(frame, orient="horizontal").pack(fill="x", padx=16, pady=2)
        self._edu_panel = EntryPanel(frame, EducationEntry)
        self._edu_panel.pack(fill="both", expand=True, padx=8, pady=4)
        return frame

    # ── Tab 3: Experience ───────────────────────────────────────────── #

    def _build_tab_experience(self) -> ttk.Frame:
        frame = ttk.Frame(self._notebook)
        tk.Label(frame, text="Work Experience", font=FONT_LARGE,
                 bg=PALETTE["bg"], fg=PALETTE["heading"]).pack(anchor="w", padx=16, pady=(8, 4))
        ttk.Separator(frame, orient="horizontal").pack(fill="x", padx=16, pady=2)
        self._exp_panel = EntryPanel(frame, ExperienceEntry)
        self._exp_panel.pack(fill="both", expand=True, padx=8, pady=4)
        return frame

    # ── Tab 4: Skills ───────────────────────────────────────────────── #

    def _build_tab_skills(self) -> ttk.Frame:
        frame = ttk.Frame(self._notebook)
        inner = tk.Frame(frame, bg=PALETTE["bg"])
        inner.pack(fill="both", expand=True, padx=16, pady=8)

        tk.Label(inner, text="Skills", font=FONT_LARGE,
                 bg=PALETTE["bg"], fg=PALETTE["heading"]).pack(anchor="w")
        ttk.Separator(inner, orient="horizontal").pack(fill="x", pady=4)

        tk.Label(
            inner,
            text="Enter each category as a comma-separated list.",
            font=FONT_NORMAL, bg=PALETTE["bg"], fg="#666666",
        ).pack(anchor="w", pady=(0, 8))

        self._tech_skills = LabeledTextArea(
            inner,
            "Technical Skills  (e.g. Python, SQL, Docker, React, AWS, Machine Learning)",
            height=4,
        )
        self._tech_skills.pack(fill="x")

        self._soft_skills = LabeledTextArea(
            inner,
            "Soft Skills  (e.g. Leadership, Communication, Problem-solving, Agile)",
            height=3,
        )
        self._soft_skills.pack(fill="x")

        self._tools = LabeledTextArea(
            inner,
            "Tools & Technologies  (e.g. Git, Jira, Figma, Jupyter, Terraform)",
            height=3,
        )
        self._tools.pack(fill="x")

        return frame

    # ── Tab 5: Projects ─────────────────────────────────────────────── #

    def _build_tab_projects(self) -> ttk.Frame:
        frame = ttk.Frame(self._notebook)
        tk.Label(frame, text="Projects", font=FONT_LARGE,
                 bg=PALETTE["bg"], fg=PALETTE["heading"]).pack(anchor="w", padx=16, pady=(8, 4))
        ttk.Separator(frame, orient="horizontal").pack(fill="x", padx=16, pady=2)
        self._proj_panel = EntryPanel(frame, ProjectEntry)
        self._proj_panel.pack(fill="both", expand=True, padx=8, pady=4)
        return frame

    # ── Tab 6: Generate & Score ─────────────────────────────────────── #

    def _build_tab_generate(self) -> ttk.Frame:
        frame = ttk.Frame(self._notebook)
        inner = tk.Frame(frame, bg=PALETTE["bg"])
        inner.pack(fill="both", expand=True, padx=16, pady=8)

        tk.Label(inner, text="Generate & Optimise", font=FONT_LARGE,
                 bg=PALETTE["bg"], fg=PALETTE["heading"]).pack(anchor="w")
        ttk.Separator(inner, orient="horizontal").pack(fill="x", pady=4)

        # Job targeting
        jt_frame = tk.LabelFrame(
            inner, text="ATS Targeting", font=FONT_BOLD,
            bg=PALETTE["bg"], fg=PALETTE["heading"], padx=8, pady=6,
        )
        jt_frame.pack(fill="x", pady=(0, 8))

        self._job_title = LabeledEntry(
            jt_frame,
            "Target Job Title  (used to recommend keywords)",
            "e.g. Software Engineer / Data Scientist / Product Manager",
        )
        self._job_title.pack(fill="x")

        self._job_desc = LabeledTextArea(
            jt_frame,
            "Job Description  (optional — paste for deeper keyword matching)",
            height=5,
        )
        self._job_desc.pack(fill="x")

        # Action buttons
        btn_frame = tk.Frame(inner, bg=PALETTE["bg"])
        btn_frame.pack(fill="x", pady=6)

        _make_button(btn_frame, "  Score ATS  ",      self._run_score, bg="#27ae60").pack(side="left", padx=4)
        _make_button(btn_frame, "  Export PDF  ",     self._run_pdf).pack(side="left", padx=4)
        _make_button(btn_frame, "  Export DOCX  ",    self._run_docx).pack(side="left", padx=4)
        _make_button(btn_frame, "  Save JSON  ",      self._save_json, bg="#8e44ad").pack(side="left", padx=4)
        _make_button(btn_frame, "  Load Version  ",   self._load_version, bg="#2c3e50").pack(side="left", padx=4)

        # Score display
        score_frame = tk.LabelFrame(
            inner, text="ATS Score Report", font=FONT_BOLD,
            bg=PALETTE["bg"], fg=PALETTE["heading"], padx=8, pady=6,
        )
        score_frame.pack(fill="both", expand=True, pady=(4, 0))

        self._score_display = scrolledtext.ScrolledText(
            score_frame, font=FONT_MONO, height=16,
            bg="#1e1e2e", fg="#cdd6f4", relief="flat",
            wrap=tk.WORD, state="disabled",
        )
        self._score_display.pack(fill="both", expand=True)

        return frame

    # ------------------------------------------------------------------ #
    #  Status bar                                                          #
    # ------------------------------------------------------------------ #

    def _build_status_bar(self) -> None:
        self._status_var = tk.StringVar(value="Ready.")
        bar = tk.Label(
            self._root, textvariable=self._status_var,
            font=("Segoe UI", 9), bg="#dddddd", fg="#333333",
            anchor="w", padx=10, relief="sunken",
        )
        bar.pack(fill="x", side="bottom")

    # ------------------------------------------------------------------ #
    #  Data collection from all tabs                                       #
    # ------------------------------------------------------------------ #

    def _collect_cv_data(self) -> Dict[str, Any]:
        """Read all widget values and assemble the CV dict."""

        def _parse_csv(text: str) -> List[str]:
            return [t.strip() for t in text.replace("\n", ",").split(",") if t.strip()]

        return {
            "personal": {
                "name":     self._name.get(),
                "email":    self._email.get(),
                "phone":    self._phone.get(),
                "linkedin": self._linkedin.get(),
                "github":   self._github.get(),
                "location": self._location.get(),
                "website":  self._website.get(),
                "summary":  self._summary.get(),
            },
            "education":      self._edu_panel.get_all(),
            "experience":     self._exp_panel.get_all(),
            "skills": {
                "technical": _parse_csv(self._tech_skills.get()),
                "soft":      _parse_csv(self._soft_skills.get()),
                "tools":     _parse_csv(self._tools.get()),
            },
            "projects":       self._proj_panel.get_all(),
            "certifications": [],
            "meta":           {},
        }

    def _process_cv_data(self, job_title: str, job_desc: str) -> Dict[str, Any]:
        """
        Run the full processing pipeline:
        validate → normalise → optimise → score → suggest.
        Returns the enriched cv_data dict.
        """
        raw_data = self._collect_cv_data()

        validator = DataValidator()
        data = validator.validate(raw_data)

        normalizer = SkillNormalizer()
        data = normalizer.normalize(data)

        optimizer = ATSOptimizer()
        data = optimizer.optimize(data, job_title, job_desc or None)

        scorer = ATSScorer()
        scorer.score(data)   # result stored in data["meta"]["ats_score_report"]

        suggester = ImprovementSuggester()
        suggestions = suggester.suggest(data)
        data["meta"]["suggestions"] = suggestions

        return data

    # ------------------------------------------------------------------ #
    #  Button actions                                                      #
    # ------------------------------------------------------------------ #

    def _run_score(self) -> None:
        """Validate, process, score the CV and display results."""
        self._set_status("Scoring CV…")

        def _work():
            try:
                job_title = self._job_title.get()
                job_desc  = self._job_desc.get()
                data = self._process_cv_data(job_title, job_desc)
                self._last_cv_data = data
                self._root.after(0, lambda: self._display_score(data))
                self._root.after(0, lambda: self._set_status("Scoring complete."))
            except Exception as exc:
                self._root.after(0, lambda: messagebox.showerror("Error", str(exc)))
                self._root.after(0, lambda: self._set_status("Error during scoring."))

        threading.Thread(target=_work, daemon=True).start()

    def _run_pdf(self) -> None:
        """Generate and save the PDF CV."""
        self._set_status("Generating PDF…")

        def _work():
            try:
                job_title = self._job_title.get()
                job_desc  = self._job_desc.get()
                data = self._process_cv_data(job_title, job_desc)
                self._last_cv_data = data

                builder = PDFBuilder()
                path = builder.build(data, self._output_dir)
                self._root.after(0, lambda: messagebox.showinfo(
                    "PDF Saved", f"PDF CV saved to:\n{os.path.abspath(path)}"
                ))
                self._root.after(0, lambda: self._set_status(f"PDF saved: {path}"))
                self._root.after(0, lambda: self._display_score(data))
            except Exception as exc:
                self._root.after(0, lambda: messagebox.showerror("PDF Error", str(exc)))
                self._root.after(0, lambda: self._set_status("PDF generation failed."))

        threading.Thread(target=_work, daemon=True).start()

    def _run_docx(self) -> None:
        """Generate and save the DOCX CV."""
        self._set_status("Generating DOCX…")

        def _work():
            try:
                from src.builder.docx_builder import DOCXBuilder
                job_title = self._job_title.get()
                job_desc  = self._job_desc.get()
                data = self._process_cv_data(job_title, job_desc)
                self._last_cv_data = data

                builder = DOCXBuilder()
                path = builder.build(data, self._output_dir)
                self._root.after(0, lambda: messagebox.showinfo(
                    "DOCX Saved", f"DOCX CV saved to:\n{os.path.abspath(path)}"
                ))
                self._root.after(0, lambda: self._set_status(f"DOCX saved: {path}"))
            except ImportError:
                self._root.after(0, lambda: messagebox.showwarning(
                    "Missing Dependency",
                    "python-docx is not installed.\nRun: pip install python-docx",
                ))
                self._root.after(0, lambda: self._set_status("DOCX unavailable (python-docx missing)."))
            except Exception as exc:
                self._root.after(0, lambda: messagebox.showerror("DOCX Error", str(exc)))
                self._root.after(0, lambda: self._set_status("DOCX generation failed."))

        threading.Thread(target=_work, daemon=True).start()

    def _save_json(self) -> None:
        """Save the current CV as a versioned JSON file."""
        if not self._last_cv_data:
            # Process first
            try:
                job_title = self._job_title.get()
                job_desc  = self._job_desc.get()
                self._last_cv_data = self._process_cv_data(job_title, job_desc)
            except Exception as exc:
                messagebox.showerror("Error", str(exc))
                return

        label = tk.simpledialog.askstring(
            "Version Label",
            "Optional version label (e.g. 'senior_role', 'v2'):",
            parent=self._root,
        )
        path = self._json_builder.build(
            self._last_cv_data,
            version_label=label or None,
        )
        messagebox.showinfo("JSON Saved", f"Saved to:\n{os.path.abspath(path)}")
        self._set_status(f"JSON saved: {path}")

    def _load_version(self) -> None:
        """Let the user pick a saved JSON version and populate all tabs."""
        versions = self._json_builder.list_versions()
        if not versions:
            messagebox.showinfo("No Versions", "No saved CV versions found in the output folder.")
            return

        # Show a selection dialog
        dialog = _VersionPickerDialog(self._root, versions)
        self._root.wait_window(dialog)
        selected = dialog.result
        if not selected:
            return

        data = self._json_builder.load_version(selected)
        if data is None:
            messagebox.showerror("Load Error", f"Could not load: {selected}")
            return

        self._populate_from_data(data)
        self._last_cv_data = data
        self._set_status(f"Loaded version: {selected}")

    # ------------------------------------------------------------------ #
    #  Populate GUI from loaded data                                       #
    # ------------------------------------------------------------------ #

    def _populate_from_data(self, data: Dict[str, Any]) -> None:
        """Fill all tab widgets from a cv_data dict (e.g. loaded from JSON)."""
        personal = data.get("personal", {})
        self._name.set(personal.get("name", ""))
        self._email.set(personal.get("email", ""))
        self._phone.set(personal.get("phone", ""))
        self._linkedin.set(personal.get("linkedin", ""))
        self._github.set(personal.get("github", ""))
        self._location.set(personal.get("location", ""))
        self._website.set(personal.get("website", ""))
        self._summary.set(personal.get("summary", ""))

        self._edu_panel.set_all(data.get("education", []))
        self._exp_panel.set_all(data.get("experience", []))
        self._proj_panel.set_all(data.get("projects", []))

        skills = data.get("skills", {})
        self._tech_skills.set(", ".join(skills.get("technical", [])))
        self._soft_skills.set(", ".join(skills.get("soft", [])))
        self._tools.set(", ".join(skills.get("tools", [])))

        meta = data.get("meta", {})
        self._job_title.set(meta.get("target_job_title", ""))

    # ------------------------------------------------------------------ #
    #  Score display                                                       #
    # ------------------------------------------------------------------ #

    def _display_score(self, data: Dict[str, Any]) -> None:
        """Render the ATS score report and suggestions into the text widget."""
        report      = data.get("meta", {}).get("ats_score_report", {})
        suggestions = data.get("meta", {}).get("suggestions", [])
        opt         = data.get("meta", {}).get("ats_optimization", {})

        lines: List[str] = []

        # ── Score summary ──
        total = report.get("total_score", 0)
        grade = report.get("grade", "?")
        bar   = self._score_bar(total)
        lines += [
            "━" * 58,
            f"  ATS SCORE:  {total}/100   Grade: {grade}   {bar}",
            "━" * 58,
            "",
        ]

        # ── Breakdown ──
        lines.append("SCORE BREAKDOWN")
        lines.append("─" * 42)
        for dim, details in report.get("breakdown", {}).items():
            pts  = details.get("score", 0)
            mx   = details.get("max",   0)
            msg  = details.get("message", "")
            fill = int(pts / mx * 12) if mx else 0
            bar2 = "█" * fill + "░" * (12 - fill)
            lines.append(f"  {dim:<25}  {pts:>2}/{mx}  [{bar2}]")
            lines.append(f"             {msg}")
        lines.append("")

        # ── Keyword coverage ──
        if opt:
            cov     = opt.get("keyword_coverage_pct", 0)
            matched = opt.get("matched_keywords", [])
            missing = opt.get("missing_keywords", [])[:8]
            lines += [
                f"KEYWORD COVERAGE: {cov:.1f}%  ({len(matched)} matched)",
                f"TOP MISSING:  {', '.join(missing) if missing else 'None — great job!'}",
                "",
            ]

        # ── Improvement suggestions ──
        if suggestions:
            lines.append(f"IMPROVEMENT SUGGESTIONS  ({len(suggestions)} found)")
            lines.append("─" * 42)
            for i, s in enumerate(suggestions, 1):
                priority = s.get("priority", "low").upper()
                lines.append(f"  {i}. [{priority}]  {s.get('message', '')}")
                lines.append("")
        else:
            lines.append("No major issues found — your CV looks strong!")

        # Write to display
        text = "\n".join(lines)
        self._score_display.config(state="normal")
        self._score_display.delete("1.0", tk.END)
        self._score_display.insert("1.0", text)
        self._score_display.config(state="disabled")

        # Switch to Generate tab
        self._notebook.select(5)

    # ------------------------------------------------------------------ #
    #  Helpers                                                             #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _score_bar(score: int, width: int = 20) -> str:
        fill = int(score / 100 * width)
        return "[" + "█" * fill + "░" * (width - fill) + "]"

    def _set_status(self, msg: str) -> None:
        self._status_var.set(msg)

    def _show_about(self) -> None:
        messagebox.showinfo(
            "About ATS CV Generator",
            "ATS CV Generator v1.0\n\n"
            "Generates ATS-optimised CVs in PDF, DOCX, and JSON formats.\n"
            "Uses rule-based analysis — no external AI APIs.\n\n"
            "Built with Python + ReportLab + Tkinter.",
        )

    # ------------------------------------------------------------------ #
    #  Run                                                                 #
    # ------------------------------------------------------------------ #

    def run(self) -> None:
        """Start the Tkinter main loop."""
        self._root.mainloop()


# ─────────────────────────────────────────────────────────────────────── #
#  Version picker dialog                                                   #
# ─────────────────────────────────────────────────────────────────────── #

class _VersionPickerDialog(tk.Toplevel):
    """Simple modal dialog listing saved CV versions."""

    def __init__(self, parent, versions: List[Dict[str, str]]) -> None:
        super().__init__(parent)
        self.title("Load Saved Version")
        self.geometry("540x320")
        self.resizable(False, False)
        self.grab_set()
        self.result: Optional[str] = None

        tk.Label(self, text="Select a saved CV version:", font=FONT_BOLD).pack(pady=8)

        listbox_frame = tk.Frame(self)
        listbox_frame.pack(fill="both", expand=True, padx=12)

        sb = tk.Scrollbar(listbox_frame)
        sb.pack(side="right", fill="y")

        self._lb = tk.Listbox(
            listbox_frame, yscrollcommand=sb.set,
            font=FONT_NORMAL, selectmode="single", height=10,
        )
        self._lb.pack(fill="both", expand=True)
        sb.config(command=self._lb.yview)

        self._filenames: List[str] = []
        for v in versions:
            label = (
                f"{v['filename']}  —  {v.get('name', '')}  "
                f"({v.get('exported_at', '')[:10]})"
            )
            self._lb.insert(tk.END, label)
            self._filenames.append(v["filename"])

        btn_row = tk.Frame(self)
        btn_row.pack(pady=8)
        tk.Button(btn_row, text="Load", command=self._on_load, font=FONT_BOLD,
                  bg=PALETTE["btn_bg"], fg=PALETTE["btn_fg"], padx=10).pack(side="left", padx=6)
        tk.Button(btn_row, text="Cancel", command=self.destroy, font=FONT_BOLD,
                  padx=10).pack(side="left", padx=6)

    def _on_load(self) -> None:
        sel = self._lb.curselection()
        if sel:
            self.result = self._filenames[sel[0]]
        self.destroy()


# ─────────────────────────────────────────────────────────────────────── #
#  Ensure simpledialog is available                                        #
# ─────────────────────────────────────────────────────────────────────── #
try:
    from tkinter import simpledialog  # noqa: F401 — imported for side effect
except ImportError:
    pass
