
# -*- coding: utf-8 -*-
"""
base.py - מחלקת בסיס למסכים + תבנית פריסה
"""
import tkinter as tk
from tkinter import ttk

class BasePage(ttk.Frame):
    def __init__(self, parent, controller, title: str):
        super().__init__(parent, padding=16)
        self.controller = controller
        self.title_lbl = ttk.Label(self, text=title, style="Title.TLabel")
        self.title_lbl.pack(anchor="w", pady=(0,12))

        self.card = ttk.Frame(self, style="Card.TFrame", padding=16)
        self.card.pack(fill="both", expand=True)

    def on_show(self):
        pass
