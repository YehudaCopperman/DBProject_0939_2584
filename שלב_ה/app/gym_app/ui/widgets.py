# -*- coding: utf-8 -*-
"""
widgets.py - Reusable UI widgets: SearchBar, PaginationBar (language-agnostic)
"""
import tkinter as tk
from tkinter import ttk
from math import ceil


class SearchBar(ttk.Frame):
    """
    A compact search bar with an Entry + 'Search' button.
    - Language-agnostic placeholder support.
    - Pressing Enter triggers the search.
    """
    def __init__(self, parent, on_search, placeholder="Search...", **kw):
        super().__init__(parent, **kw)
        self.on_search = on_search
        self._placeholder = placeholder
        self._has_placeholder = False

        self.var = tk.StringVar()
        self.entry = ttk.Entry(self, textvariable=self.var, width=30)
        self.entry.pack(side=tk.LEFT, padx=(0, 6))

        ttk.Button(self, text="Search", style="Primary.TButton", command=self._do).pack(side=tk.LEFT)

        # Placeholder handling
        self._set_placeholder()
        self.entry.bind("<FocusIn>", self._on_focus_in)
        self.entry.bind("<FocusOut>", self._on_focus_out)
        self.entry.bind("<Return>", lambda _e: self._do())

    def _set_placeholder(self):
        self.entry.delete(0, tk.END)
        self.entry.insert(0, self._placeholder)
        self._has_placeholder = True

    def _on_focus_in(self, _):
        if self._has_placeholder:
            self.entry.delete(0, tk.END)
            self._has_placeholder = False

    def _on_focus_out(self, _):
        if not self.entry.get().strip():
            self._set_placeholder()

    def _do(self):
        text = "" if self._has_placeholder else self.var.get()
        self.on_search(text)


class PaginationBar(ttk.Frame):
    """
    Simple Prev/Next pager:
    - Shows "Page X of Y"
    - Calls on_page_change(new_page) when navigation occurs
    """
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

        total_pages = max(1, ceil(self.total / self.page_size)) if self.total else 1

        ttk.Button(
            self, text="◀ Prev", style="Ghost.TButton",
            command=lambda: self._go(max(1, self.page - 1))
        ).pack(side=tk.LEFT, padx=3)

        ttk.Label(
            self, text=f"Page {self.page} of {total_pages}", style="SubTitle.TLabel"
        ).pack(side=tk.LEFT, padx=8)

        ttk.Button(
            self, text="Next ▶", style="Ghost.TButton",
            command=lambda: self._go(min(total_pages, self.page + 1))
        ).pack(side=tk.LEFT, padx=3)

    def _go(self, page: int):
        if page != self.page:
            self.page = page
            self.on_page_change(page)
            self._build()
