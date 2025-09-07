# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox
from ..ui.base import BasePage
from ..ui.widgets import SearchBar, PaginationBar
from .. import dao
from ..config import PAGE_SIZE


class MembersPage(BasePage):
    """Read-only members view with search and pagination."""

    def __init__(self, parent, controller):
        super().__init__(parent, controller, "Members")

        # Top bar: search + refresh
        top = ttk.Frame(self.card, style="Card.TFrame", padding=(0, 4, 0, 8))
        top.pack(fill="x")
        self.search_bar = SearchBar(top, on_search=self._on_search, placeholder="Search by name or PID...")
        self.search_bar.pack(side="left")
        ttk.Button(top, text="Refresh", style="Ghost.TButton", command=lambda: self._load()).pack(side="right")

        # Table
        table_frame = ttk.Frame(self.card, padding=(0, 8, 0, 0), style="Card.TFrame")
        table_frame.pack(fill="both", expand=True)

        cols = ("pid", "firstname", "lastname", "membershiptype", "memberstartdate", "isactive")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c)
            # Wider name columns, tighter for flags/dates
            width = 150 if c in ("firstname", "lastname", "membershiptype") else (120 if c != "isactive" else 90)
            self.tree.column(c, width=width, anchor="center")
        self.tree.pack(side="left", fill="both", expand=True)

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")

        # Pagination
        self.page = 1
        self.total = 0
        self._current_search = ""
        self.pager = PaginationBar(
            self.card,
            on_page_change=self._goto_page,
            page=self.page,
            total=self.total,
            page_size=PAGE_SIZE,
        )
        self.pager.pack(anchor="e", pady=(6, 0))

    # Lifecycle
    def on_show(self):
        self._load()

    # Events
    def _on_search(self, text: str):
        self._current_search = text or ""
        self.page = 1
        self._load(self._current_search)

    def _goto_page(self, page: int):
        self.page = page
        self._load(self._current_search)

    # Data
    def _load(self, search: str = ""):
        def task(conn):
            return dao.list_members(conn, search=search, page=self.page, page_size=PAGE_SIZE)

        def ok(res):
            rows, total = res
            self.total = total
            self._fill(rows)
            self.pager.total = total
            self.pager.page = self.page
            self.pager._build()

        self.controller.run_db_task(task, on_success=ok, on_error=lambda e: messagebox.showerror("Error", str(e)))

    def _fill(self, rows):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for r in rows:
            # r = (pid, firstname, lastname, membershiptype, memberstartdate, isactive)
            pid, fn, ln, mtype, start, active = r
            start_s = start.isoformat() if start else ""
            active_s = "True" if active else "False"
            self.tree.insert("", "end", values=(pid, fn, ln, mtype, start_s, active_s))
