# -*- coding: utf-8 -*-
"""
ReportsPage (read-only):
- Hours worked by month/year (aggregate)
- Most expensive service (aggregate)
No write actions are exposed here.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from ..ui.base import BasePage
from .. import dao


class ReportsPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, "Reports")

        # --- Hours by month/year ---
        row1 = ttk.Frame(self.card, padding=(0, 6, 0, 6), style="Card.TFrame")
        row1.pack(fill="x")
        ttk.Label(row1, text="Hours by Month/Year").pack(side="left", padx=(0, 8))

        ttk.Label(row1, text="Month (1-12)").pack(side="left", padx=(8, 6))
        self.month = ttk.Entry(row1, width=6)
        self.month.pack(side="left")

        ttk.Label(row1, text="Year (YYYY)").pack(side="left", padx=(12, 6))
        self.year = ttk.Entry(row1, width=8)
        self.year.pack(side="left")

        ttk.Button(
            row1, text="Run", style="Primary.TButton", command=self._run_hours
        ).pack(side="left", padx=12)

        # --- Other read-only reports ---
        row2 = ttk.Frame(self.card, padding=(0, 6, 0, 12), style="Card.TFrame")
        row2.pack(fill="x")
        ttk.Button(
            row2, text="Most Expensive Service", style="Ghost.TButton",
            command=self._run_expensive
        ).pack(side="left")

        # --- Results table ---
        table_frame = ttk.Frame(self.card, padding=(0, 8, 0, 0), style="Card.TFrame")
        table_frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(table_frame, columns=(), show="headings")
        self.tree.pack(side="left", fill="both", expand=True)

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")

    # ---------- helpers ----------
    def _set_columns(self, cols, widths=None, anchors=None):
        self.tree["columns"] = cols
        for item in self.tree.get_children():
            self.tree.delete(item)
        for i, c in enumerate(cols):
            self.tree.heading(c, text=c)
            w = (widths[i] if widths and i < len(widths) else 160)
            a = (anchors[i] if anchors and i < len(anchors) else "center")
            self.tree.column(c, width=w, anchor=a)

    # ---------- actions ----------
    def _run_hours(self):
        try:
            m = int((self.month.get() or "").strip())
            y = int((self.year.get() or "").strip())
            if not (1 <= m <= 12):
                raise ValueError("Month must be 1-12")
            if y < 1900 or y > 3000:
                raise ValueError("Year looks invalid")
        except Exception as e:
            return messagebox.showerror("Error", f"Invalid input: {e}")

        def task(conn):
            return dao.hours_by_month(conn, m, y)

        def ok(rows):
            self._set_columns(
                ("First Name", "Last Name", "Total Hours"),
                widths=[160, 160, 140],
                anchors=["center", "center", "e"]
            )
            if not rows:
                self.tree.insert("", "end", values=("No data", "", ""))
            else:
                for fn, ln, hours in rows:
                    self.tree.insert("", "end", values=(fn, ln, f"{hours:.2f}"))

        self.controller.run_db_task(task, on_success=ok, on_error=lambda e: messagebox.showerror("Error", str(e)))

    def _run_expensive(self):
        def task(conn):
            return dao.most_expensive_service(conn)

        def ok(rows):
            self._set_columns(
                ("Service Name", "Total Cost"),
                widths=[240, 140],
                anchors=["w", "e"]
            )
            if not rows:
                self.tree.insert("", "end", values=("No data", ""))
            else:
                for name, total in rows:
                    self.tree.insert("", "end", values=(name, f"{total:.2f}"))

        self.controller.run_db_task(task, on_success=ok, on_error=lambda e: messagebox.showerror("Error", str(e)))
