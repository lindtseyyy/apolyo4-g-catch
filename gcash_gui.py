#!/usr/bin/env python3
"""
GCash Receipt Cropper — Simple GUI
Place this file in the same folder as gcash_cropper.py and run:
    python gcash_gui.py
"""

import sys
import threading
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

try:
    from PIL import Image, ImageTk
except ImportError:
    messagebox.showerror("Missing", "pip install pillow")
    sys.exit(1)

sys.path.insert(0, str(Path(__file__).parent))
try:
    from cropper import process_receipt
except ImportError:
    messagebox.showerror("Missing file", "cropper.py not found in the same folder.")
    sys.exit(1)

OUT_DIR = "processed_receipts"

BG      = "#0d1117"
CARD    = "#161b27"
BORDER  = "#2a3550"
BLUE    = "#1a6aff"
BLUE_DK = "#0053e2"
GREEN   = "#00d97e"
YELLOW  = "#ffd166"
RED     = "#ff4d6d"
TEXT    = "#e8eeff"
MUTED   = "#6b7fa3"
WHITE   = "#ffffff"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("GCash Receipt Cropper")
        self.geometry("480x600")
        self.resizable(False, False)
        self.configure(bg=BG)
        self._file_path = None
        self._photo     = None
        self._build()

    def _build(self):
        # Title bar
        bar = tk.Frame(self, bg=CARD, height=52)
        bar.pack(fill="x")
        bar.pack_propagate(False)
        tk.Label(bar, text="GCash", font=("Helvetica", 14, "bold"),
                 bg=CARD, fg=BLUE).pack(side="left", padx=(16, 0), pady=14)
        tk.Label(bar, text=" Receipt Cropper", font=("Helvetica", 14),
                 bg=CARD, fg=TEXT).pack(side="left", pady=14)

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=24, pady=20)

        # Upload button
        tk.Button(
            body, text="📂  Choose Receipt Image",
            font=("Helvetica", 11, "bold"), bg=BLUE, fg=WHITE,
            activebackground=BLUE_DK, activeforeground=WHITE,
            relief="flat", cursor="hand2", pady=12,
            command=self._pick
        ).pack(fill="x")

        # File name
        self._file_lbl = tk.Label(body, text="No file selected",
                                   font=("Courier", 9), bg=BG, fg=MUTED)
        self._file_lbl.pack(pady=(6, 0))

        # Preview box
        pf = tk.Frame(body, bg=CARD, highlightthickness=1,
                      highlightbackground=BORDER)
        pf.pack(fill="both", expand=True, pady=16)
        tk.Label(pf, text="PREVIEW", font=("Courier", 8),
                 bg=CARD, fg=MUTED).pack(pady=(8, 0))
        self._canvas = tk.Canvas(pf, bg=CARD, highlightthickness=0,
                                  width=420, height=340)
        self._canvas.pack(padx=8, pady=(4, 8))

        # Process button
        self._proc_btn = tk.Button(
            body, text="⚙  Process Receipt",
            font=("Helvetica", 11, "bold"), bg=CARD, fg=MUTED,
            activebackground=BLUE_DK, activeforeground=WHITE,
            relief="flat", cursor="hand2", pady=12,
            state="disabled", command=self._process
        )
        self._proc_btn.pack(fill="x")

        # Status
        self._status = tk.Label(body, text="", font=("Courier", 10, "bold"),
                                 bg=BG, fg=MUTED, justify="center")
        self._status.pack(pady=(10, 0))

    def _pick(self):
        path = filedialog.askopenfilename(
            title="Select GCash Receipt",
            filetypes=[("Images", "*.jpg *.jpeg *.png"), ("All", "*.*")]
        )
        if not path:
            return
        self._file_path = path
        self._file_lbl.config(text=Path(path).name, fg=TEXT)
        self._proc_btn.config(state="normal", bg=BLUE, fg=WHITE)
        self._status.config(text="")
        self._load_preview(path)

    def _load_preview(self, path):
        try:
            img = Image.open(path)
            img.thumbnail((420, 340), Image.LANCZOS)
            self._photo = ImageTk.PhotoImage(img)
            self._canvas.delete("all")
            self._canvas.create_image(210, 170, anchor="center", image=self._photo)
        except Exception:
            pass

    def _process(self):
        self._proc_btn.config(state="disabled", bg=CARD, fg=MUTED)
        self._status.config(text="Processing…", fg=YELLOW)
        self.update_idletasks()

        def _worker():
            try:
                process_receipt(self._file_path, OUT_DIR)
                out = str(Path(OUT_DIR).resolve())
                self.after(0, lambda: self._done(out))
            except Exception as e:
                self.after(0, lambda: self._error(str(e)))

        threading.Thread(target=_worker, daemon=True).start()

    def _done(self, out_path):
        self._proc_btn.config(state="normal", bg=BLUE, fg=WHITE)
        self._status.config(
            text=f"✓  Cropped successfully!\nSaved → {out_path}",
            fg=GREEN
        )

    def _error(self, msg):
        self._proc_btn.config(state="normal", bg=BLUE, fg=WHITE)
        self._status.config(text=f"✗  Error: {msg}", fg=RED)
        messagebox.showerror("Error", msg)


if __name__ == "__main__":
    App().mainloop()