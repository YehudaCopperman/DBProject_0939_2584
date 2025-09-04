# -*- coding: utf-8 -*-
"""
PersonsPage (read-only):
- Search by name or PID
- Paginated results
- No create/update/delete actions (view-only)
"""
import tkinter as tk
from tkinter import ttk, messagebox

from ..ui.base import BasePage
from ..ui.widgets import SearchBar, PaginationBar
from .. import dao
from ..config import PAGE_SIZE


class PersonsPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, "אנשים (קריאה בלבד)")
        # Top bar: search + refresh
        top = ttk.Frame(self.card, style="Card.TFrame")
        top.pack(fill="x")

        self.search_bar = SearchBar(top, on_search=self._do_search, placeholder="חפש לפי שם או ת.ז...")
        self.search_bar.pack(side="left")

        ttk.Button(top, text="רענן", style="Ghost.TButton",
                   command=lambda: self._load()).pack(side="right")

        # Table (read-only)
        table_frame = ttk.Frame(self.card, padding=(0, 8, 0, 0), style="Card.TFrame")
        table_frame.pack(fill="both", expand=True)

        self.columns = ("pid", "firstname", "lastname", "dateofb", "email", "address", "phone")
        self.tree = ttk.Treeview(table_frame, columns=self.columns, show="headings", selectmode="browse")
        for c in self.columns:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=140, anchor="center")
        self.tree.pack(side="left", fill="both", expand=True)

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")

        # Pagination
        self.page = 1
        self.total = 0
        self.pager = PaginationBar(self.card, on_page_change=self._goto_page,
                                   page=self.page, total=self.total, page_size=PAGE_SIZE)
        self.pager.pack(anchor="e", pady=(6, 0))

    # Lifecycle
    def on_show(self):
        self._load()

    # Paging + search
    def _goto_page(self, page: int):
        self.page = page
        self._load()

    def _do_search(self, txt: str):
        self.page = 1
        self._load(txt)

    # Data load
    def _load(self, search: str = ""):
        def task(conn):
            return dao.list_persons(conn, search=search, page=self.page, page_size=PAGE_SIZE)

        def ok(res):
            rows, total = res
            self.total = total
            self._fill(rows)
            self.pager.total = total
            self.pager.page = self.page
            self.pager._build()

        self.controller.run_db_task(task, on_success=ok, on_error=self._err)

    # Rendering
    def _fill(self, rows):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for r in rows:
            # dateofb to ISO if not None
            row = list(r)
            row[3] = row[3].isoformat() if row[3] else ""
            self.tree.insert("", "end", values=tuple(row))

    # Errors
    def _err(self, e: Exception):
        messagebox.showerror("שגיאה", str(e))
