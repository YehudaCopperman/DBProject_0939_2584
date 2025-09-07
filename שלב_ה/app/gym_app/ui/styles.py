# -*- coding: utf-8 -*-
"""
styles.py - Global modern look & feel for the Gym GUI
- Apple-like clean palette
- Consistent typography
- Subtle hover/pressed states
- Card surfaces and comfortable spacing
"""

import tkinter as tk
from tkinter import ttk
from ..config import THEME


def setup_styles(root: tk.Tk):
    style = ttk.Style(root)

    # ----- Theme base -----
    try:
        style.theme_use(THEME)  # "clam" by default (good for macOS)
    except tk.TclError:
        # Fallback to current default if "clam" isn't available
        pass

    # ----- Palette (light, friendly, “Apple-ish”) -----
    # Base surfaces
    bg      = "#f5f7fb"   # App background
    card    = "#ffffff"   # Cards / containers
    text    = "#0f172a"   # Primary text
    subtle  = "#64748b"   # Secondary text

    # Accents
    primary = "#0a84ff"   # iOS/macOS accent-ish blue
    primary_hover   = "#066bd1"
    primary_pressed = "#0454a6"

    danger  = "#dc2626"
    danger_hover   = "#b91c1c"
    danger_pressed = "#991b1b"

    # Treeview tones
    tv_bg       = "#ffffff"
    tv_field_bg = "#ffffff"
    tv_grid     = "#e5e7eb"

    # Apply window bg
    root.configure(bg=bg)

    # ----- Base widgets -----
    style.configure("TFrame", background=bg)
    style.configure("Toolbar.TFrame", background=bg, padding=0)
    style.configure("Card.TFrame", background=card, relief="flat", borderwidth=0)

    style.configure(
        "TLabel",
        background=bg,
        foreground=text,
        font=("SF Pro Text", 12),
    )
    style.configure(
        "Title.TLabel",
        background=bg,
        foreground=text,
        font=("SF Pro Display", 22, "bold"),
    )
    style.configure(
        "SubTitle.TLabel",
        background=bg,
        foreground=subtle,
        font=("SF Pro Text", 11),
    )

    # Entries
    style.configure(
        "TEntry",
        fieldbackground="#ffffff",
        bordercolor="#cbd5e1",
        lightcolor="#cbd5e1",
        darkcolor="#94a3b8",
        padding=6,
        relief="flat",
    )

    # ----- Buttons -----
    # Primary (filled)
    style.configure(
        "Primary.TButton",
        padding=(14, 7),
        font=("SF Pro Text", 12, "bold"),
        background=primary,
        foreground="#ffffff",
        borderwidth=0,
        relief="flat",
    )
    style.map(
        "Primary.TButton",
        background=[("active", primary_hover), ("pressed", primary_pressed)],
        foreground=[("disabled", "#e5e7eb")],
    )

    # Ghost (text-like)
    style.configure(
        "Ghost.TButton",
        padding=(12, 6),
        font=("SF Pro Text", 12),
        background=card,
        foreground=primary,
        borderwidth=0,
        relief="flat",
    )
    style.map(
        "Ghost.TButton",
        foreground=[("active", primary_hover), ("pressed", primary_pressed)],
        background=[("active", card)],
    )

    # Danger
    style.configure(
        "Danger.TButton",
        padding=(14, 7),
        font=("SF Pro Text", 12, "bold"),
        background=danger,
        foreground="#ffffff",
        borderwidth=0,
        relief="flat",
    )
    style.map(
        "Danger.TButton",
        background=[("active", danger_hover), ("pressed", danger_pressed)],
        foreground=[("disabled", "#f3f4f6")],
    )

    # Navigation (full-width feel, left aligned)
    style.configure(
        "Nav.TButton",
        padding=(12, 10),
        anchor="w",
        font=("SF Pro Text", 12, "bold"),
        background=card,
        foreground=text,
        borderwidth=0,
        relief="flat",
    )
    style.map(
        "Nav.TButton",
        background=[("active", "#eef2f7")],
        foreground=[("active", text)],
    )

    # ----- Treeview (tables) -----
    style.configure(
        "Treeview",
        background=tv_bg,
        fieldbackground=tv_field_bg,
        foreground=text,
        rowheight=28,
        font=("SF Pro Text", 12),
        bordercolor=tv_grid,
        lightcolor=tv_grid,
        darkcolor=tv_grid,
    )
    style.configure(
        "Treeview.Heading",
        font=("SF Pro Text", 12, "bold"),
        background="#f3f4f6",
        foreground=text,
        relief="flat",
        borderwidth=0,
        padding=(6, 8),
    )
    style.map(
        "Treeview.Heading",
        background=[("active", "#e5e7eb")],
    )

    # Scrollbars (subtle)
    style.configure("Vertical.TScrollbar", background=bg)
    style.configure("Horizontal.TScrollbar", background=bg)

    # Separators
    style.configure("TSeparator", background="#e2e8f0")
