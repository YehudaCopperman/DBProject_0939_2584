
# -*- coding: utf-8 -*-
"""
widgets.py - ווידג'טים חוזרים: סרגל חיפוש, פאג'ינציה
"""
import tkinter as tk
from tkinter import ttk
from math import ceil

class SearchBar(ttk.Frame):
    def __init__(self, parent, on_search, placeholder="חיפוש...", **kw):
        super().__init__(parent, **kw)
        self.on_search = on_search
        self.var = tk.StringVar()
        self.entry = ttk.Entry(self, textvariable=self.var, width=30)
        self.entry.pack(side=tk.LEFT, padx=(0,6))
        ttk.Button(self, text="חפש", style="Primary.TButton", command=self._do).pack(side=tk.LEFT)
        self.entry.bind("<Return>", lambda e: self._do())
        self._set_placeholder(placeholder)

    def _set_placeholder(self, text):
        self.entry.insert(0, text)
        self.entry.bind("<FocusIn>", self._clear_placeholder)
        self.entry.bind("<FocusOut>", lambda e: self._restore_placeholder(text))

    def _clear_placeholder(self, _):
        if self.entry.get().startswith("חיפוש"):
            self.entry.delete(0, tk.END)

    def _restore_placeholder(self, text):
        if not self.entry.get():
            self.entry.insert(0, text)

    def _do(self):
        self.on_search(self.var.get())

class PaginationBar(ttk.Frame):
    def __init__(self, parent, on_page_change, page=1, total=0, page_size=50, **kw):
        super().__init__(parent, **kw)
        self.on_page_change = on_page_change
        self.page = page
        self.page_size = page_size
        self.total = total
        self._build()

    def _build(self):
        for w in self.winfo_children():
            w.destroy()
        pages = max(1, ceil(self.total / self.page_size)) if self.total else 1
        ttk.Button(self, text="◀ הקודם", style="Ghost.TButton",
                   command=lambda: self._go(max(1, self.page-1))).pack(side=tk.LEFT, padx=3)
        ttk.Label(self, text=f"עמוד {self.page} מתוך {pages}", style="SubTitle.TLabel").pack(side=tk.LEFT, padx=8)
        ttk.Button(self, text="הבא ▶", style="Ghost.TButton",
                   command=lambda: self._go(min(pages, self.page+1))).pack(side=tk.LEFT, padx=3)

    def _go(self, page: int):
        if page != self.page:
            self.page = page
            self.on_page_change(page)
            self._build()
