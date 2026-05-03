import sys
import os
import tkinter as tk
from tkinter import filedialog, messagebox

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.cv_parser import extract_text_from_cv
from services.analysis_service import analyze_profile


def browse_file():
    file_path = filedialog.askopenfilename(
        title="Select PDF CV",
        filetypes=[("PDF files", "*.pdf")]
    )
    if file_path:
        path_entry.delete(0, tk.END)
        path_entry.insert(0, file_path)


def analyze_cv():
    file_path = path_entry.get()
    if not file_path:
        messagebox.showwarning("No file", "Please select a CV file first!")
        return

    try:
        cv_text = extract_text_from_cv(file_path)
        if not cv_text.strip():
            messagebox.showwarning("Empty file", "The selected PDF is empty.")
            return

        result = analyze_profile(cv_text)

        result_text = f"Score: {result['score']}\n"
        result_text += f"Price Range: {result['price_range']}\n"
        result_text += "Suggested Campaigns:\n"
        for c in result["allowed_campaigns"]:
            result_text += f"- {c}\n"

        output_text.delete("1.0", tk.END)
        output_text.insert(tk.END, result_text)

    except Exception as e:
        messagebox.showerror("Error", str(e))


# --- GUI setup ---
root = tk.Tk()
root.title("CV Analysis Tool")

tk.Label(root, text="Select PDF CV:").grid(row=0, column=0, padx=10, pady=10)
path_entry = tk.Entry(root, width=50)
path_entry.grid(row=0, column=1, padx=10, pady=10)
tk.Button(root, text="Browse", command=browse_file).grid(row=0, column=2, padx=10, pady=10)

tk.Button(root, text="Analyze CV", command=analyze_cv, width=20, bg="green", fg="white").grid(row=1, column=0, columnspan=3, pady=10)

output_text = tk.Text(root, height=15, width=70)
output_text.grid(row=2, column=0, columnspan=3, padx=10, pady=10)

root.mainloop()
