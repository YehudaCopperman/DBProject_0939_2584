import tkinter as tk
from tkinter import ttk, messagebox, Toplevel
from ..ui.base import BasePage
from ..ui.widgets import PaginationBar
from .. import dao
from ..config import PAGE_SIZE


class DataManagerPage(BasePage):
    """Generic admin data manager for whitelisted tables using information_schema introspection."""

    def __init__(self, parent, controller):
        super().__init__(parent, controller, "Data Manager")

        # Top bar: table selector + refresh
        top = ttk.Frame(self.card, padding=(0, 6, 0, 0), style="Card.TFrame")
        top.pack(fill="x")

        ttk.Label(top, text="Table").pack(side="left", padx=(0, 6))
        self.cmb_table = ttk.Combobox(top, values=dao.list_allowed_tables(), state="readonly", width=28)
        self.cmb_table.pack(side="left")
        self.cmb_table.bind("<<ComboboxSelected>>", lambda _: self._load(reset_page=True))

        ttk.Button(top, text="Refresh", style="Ghost.TButton", command=lambda: self._load(reset_page=False)).pack(side="left", padx=6)

        # Action buttons
        actions = ttk.Frame(self.card, padding=(0, 6, 0, 0), style="Card.TFrame")
        actions.pack(fill="x")
        ttk.Button(actions, text="Add", style="Primary.TButton", command=self._add).pack(side="left", padx=4)
        ttk.Button(actions, text="Edit", style="Ghost.TButton", command=self._edit).pack(side="left", padx=4)
        ttk.Button(actions, text="Delete", style="Danger.TButton", command=self._delete).pack(side="left", padx=4)

        # Table (treeview)
        table = ttk.Frame(self.card, padding=(0, 8, 0, 0), style="Card.TFrame")
        table.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(table, columns=(), show="headings")
        self.tree.pack(side="left", fill="both", expand=True)
        vsb = ttk.Scrollbar(table, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")

        # Pager
        self.page = 1
        self.total = 0
        self.pager = PaginationBar(self.card, on_page_change=self._goto_page,
                                   page=self.page, total=self.total, page_size=PAGE_SIZE)
        self.pager.pack(anchor="e", pady=6)

        # Internal state
        self._columns = []   # list[str]
        self._pk_cols = []   # list[str]
        self._current_rows = []

    def on_show(self):
        # Admin-only guard
        role = (self.controller.current_user or {}).get("role")
        if role != "admin":
            messagebox.showerror("Error", "Admin only")
            self.controller.show_frame("LoginPage")
            return

        # Set default selection once
        if not self.cmb_table.get():
            self.cmb_table.set(dao.list_allowed_tables()[0])
        self._load(reset_page=True)

    # ---------- pagination ----------
    def _goto_page(self, p: int):
        self.page = p
        self._load(reset_page=False)

    # ---------- load ----------
    def _load(self, reset_page: bool):
        table = self.cmb_table.get()
        if not table:
            return

        if reset_page:
            self.page = 1

        def task(conn):
            # columns + pk
            cols, pk = dao.get_table_columns(conn, table)
            rows, total, col_names = dao.fetch_table_rows(
                conn, table, limit=PAGE_SIZE, offset=(self.page - 1) * PAGE_SIZE
            )
            return {"cols": cols, "pk": pk, "rows": rows, "total": total, "names": col_names}

        def ok(res):
            self._columns = [c["name"] for c in res["cols"]]
            self._pk_cols = res["pk"]
            self._current_rows = res["rows"]
            self.total = res["total"]

            # rebuild tree columns
            self.tree["columns"] = self._columns
            for c in self._columns:
                self.tree.heading(c, text=c)
                self.tree.column(c, width=140, anchor="center")
            for i in self.tree.get_children():
                self.tree.delete(i)
            for r in self._current_rows:
                self.tree.insert("", "end", values=r)

            # update pager
            self.pager.total = self.total
            self.pager.page = self.page
            self.pager._build()

        self.controller.run_db_task(task, on_success=ok, on_error=lambda e: messagebox.showerror("DB Error", str(e)))

    # ---------- add/edit/delete ----------
    def _add(self):
        table = self.cmb_table.get()
        if not table:
            return
        self._open_row_dialog(table, mode="add")

    def _edit(self):
        table = self.cmb_table.get()
        if not table:
            return
        it = self.tree.focus()
        if not it:
            return messagebox.showerror("Error", "Select a row")

        values = self.tree.item(it, "values")
        row = dict(zip(self._columns, values))
        self._open_row_dialog(table, mode="edit", row=row)

    def _delete(self):
        table = self.cmb_table.get()
        if not table:
            return
        it = self.tree.focus()
        if not it:
            return messagebox.showerror("Error", "Select a row")
        values = self.tree.item(it, "values")
        row = dict(zip(self._columns, values))

        if not self._pk_cols:
            return messagebox.showerror("Error", "Table has no primary key; cannot delete")

        pk_values = {k: row[k] for k in self._pk_cols}
        if not messagebox.askyesno("Confirm", f"Delete by PK {pk_values}?"):
            return

        def task(conn):
            return dao.delete_row(conn, table, pk_values)

        self.controller.run_db_task(task,
            on_success=lambda _:(messagebox.showinfo("Success","Deleted"), self._load(reset_page=False)),
            on_error=lambda e: messagebox.showerror("DB Error", str(e))
        )

    # ---------- dialog ----------
    def _open_row_dialog(self, table: str, mode: str, row: dict | None = None):
        """
        Build a simple dynamic form for all columns.
        - In 'edit' mode, PK fields are disabled (identify row).
        - Strings are passed as-is; PostgreSQL will cast when possible (dates, ints, bools).
        """
        dlg = Toplevel(self)
        dlg.title(f"{'Add' if mode=='add' else 'Edit'} row in {table}")
        dlg.transient(self.winfo_toplevel())
        dlg.grab_set()

        frm = ttk.Frame(dlg, padding=16)
        frm.pack(fill="both", expand=True)

        entries: dict[str, ttk.Entry] = {}
        for i, col in enumerate(self._columns):
            ttk.Label(frm, text=col).grid(row=i, column=0, sticky="w", pady=4)
            e = ttk.Entry(frm, width=36)
            e.grid(row=i, column=1, pady=4, padx=(8, 0), sticky="ew")
            entries[col] = e

            if mode == "edit" and row is not None:
                e.insert(0, str(row.get(col, "")))

            if mode == "edit" and col in self._pk_cols:
                # lock PK fields in edit mode
                e.configure(state="disabled")

        frm.grid_columnconfigure(1, weight=1)

        btns = ttk.Frame(frm)
        btns.grid(row=len(self._columns), column=0, columnspan=2, sticky="e", pady=(10, 0))
        ttk.Button(btns, text="Cancel", style="Ghost.TButton", command=dlg.destroy).pack(side="left", padx=4)

        def submit():
            payload = {}
            for c, e in entries.items():
                state = str(e.cget("state"))
                if state == "disabled":
                    continue
                payload[c] = e.get().strip() or None

            if mode == "add":
                def task(conn):
                    return dao.insert_row(conn, table, payload)
                self.controller.run_db_task(
                    task,
                    on_success=lambda _:(messagebox.showinfo("Success","Created"), dlg.destroy(), self._load(reset_page=False)),
                    on_error=lambda e: messagebox.showerror("DB Error", str(e), parent=dlg),
                )
            else:
                if not self._pk_cols:
                    return messagebox.showerror("Error", "Table has no primary key; cannot update", parent=dlg)
                pk_values = {k: row[k] for k in self._pk_cols} if row else {}
                def task(conn):
                    return dao.update_row(conn, table, payload, pk_values)
                self.controller.run_db_task(
                    task,
                    on_success=lambda _:(messagebox.showinfo("Success","Updated"), dlg.destroy(), self._load(reset_page=False)),
                    on_error=lambda e: messagebox.showerror("DB Error", str(e), parent=dlg),
                )

        ttk.Button(btns, text="Save", style="Primary.TButton", command=submit).pack(side="left", padx=4)

        # Enter to save
        for e in entries.values():
            e.bind("<Return>", lambda _evt: submit())

        # Focus first editable field
        for c in self._columns:
            if mode == "add" or c not in self._pk_cols:
                entries[c].focus_set()
                break
