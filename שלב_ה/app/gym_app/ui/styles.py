
# -*- coding: utf-8 -*-
"""
styles.py - הגדרות ערכת עיצוב (ttk.Style)
"""
import tkinter as tk
from tkinter import ttk
from ..config import THEME

def setup_styles(root: tk.Tk):
    style = ttk.Style(root)
    try:
        style.theme_use(THEME)
    except tk.TclError:
        style.theme_use(style.theme_use())  # השארת ערכת ברירת מחדל

    # צבעים בסיסיים
    primary = "#2563eb"  # כחול
    danger = "#dc2626"
    bg = "#f8fafc"
    card = "#ffffff"
    text = "#0f172a"
    subtle = "#64748b"

    root.configure(bg=bg)

    style.configure("TFrame", background=bg)
    style.configure("Card.TFrame", background=card, relief="flat")
    style.configure("TLabel", background=bg, foreground=text, font=("SF Pro Text", 13))
    style.configure("Title.TLabel", background=bg, foreground=text, font=("SF Pro Display", 22, "bold"))
    style.configure("SubTitle.TLabel", background=bg, foreground=subtle, font=("SF Pro Text", 12))

    style.configure("Primary.TButton", padding=(12, 6), font=("SF Pro Text", 12, "bold"))
    style.map("Primary.TButton",
              background=[("!disabled", primary), ("pressed", "#1e40af"), ("active", "#1d4ed8")],
              foreground=[("!disabled", "white")])

    style.configure("Ghost.TButton", padding=(10, 5), font=("SF Pro Text", 12))
    style.configure("Danger.TButton", padding=(12, 6), font=("SF Pro Text", 12, "bold"))
    style.map("Danger.TButton",
              background=[("!disabled", danger), ("pressed", "#991b1b"), ("active", "#b91c1c")],
              foreground=[("!disabled", "white")])

    style.configure("Nav.TButton", padding=(10, 8), anchor="w", font=("SF Pro Text", 12))
    style.map("Nav.TButton",
              background=[("active", "#e2e8f0")])

    # עיצוב טבלאות
    style.configure("Treeview",
                    background="white",
                    fieldbackground="white",
                    rowheight=28,
                    font=("SF Pro Text", 12))
    style.configure("Treeview.Heading", font=("SF Pro Text", 12, "bold"))
