
# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
from ..ui.base import BasePage
from ..ui.widgets import SearchBar, PaginationBar
from .. import dao
from ..config import PAGE_SIZE

class PersonsPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, "ניהול אנשים (Person)")
        top = ttk.Frame(self.card, style="Card.TFrame")
        top.pack(fill="x")
        self.search_bar = SearchBar(top, on_search=self._do_search)
        self.search_bar.pack(side="left")
        ttk.Button(top, text="רענן", style="Ghost.TButton", command=lambda: self._load()).pack(side="right")

        # Form
        form = ttk.LabelFrame(self.card, text="פרטי אדם", padding=12)
        form.pack(fill="x", pady=8)
        self.inputs = {}
        fields = [("PID","pid"),("שם פרטי","firstname"),("שם משפחה","lastname"),
                  ("תאריך לידה YYYY-MM-DD","dateofb"),("Email","email"),("כתובת","address"),("טלפון","phone")]
        for i,(label, key) in enumerate(fields):
            ttk.Label(form, text=label).grid(row=i, column=0, sticky="w", pady=4)
            ent = ttk.Entry(form, width=30)
            ent.grid(row=i, column=1, sticky="ew", pady=4, padx=(8,0))
            self.inputs[key]=ent
        form.grid_columnconfigure(1, weight=1)

        btns = ttk.Frame(form)
        btns.grid(row=len(fields), column=0, columnspan=2, pady=(8,0), sticky="e")
        ttk.Button(btns, text="הוסף", style="Primary.TButton", command=self._create).pack(side="left", padx=4)
        ttk.Button(btns, text="עדכן", style="Ghost.TButton", command=self._update).pack(side="left", padx=4)
        ttk.Button(btns, text="מחק", style="Danger.TButton", command=self._delete).pack(side="left", padx=4)
        ttk.Button(btns, text="נקה", style="Ghost.TButton", command=self._clear).pack(side="left", padx=4)

        # Table
        table_frame = ttk.Frame(self.card, padding=(0,8,0,0), style="Card.TFrame")
        table_frame.pack(fill="both", expand=True)
        cols = ("pid","firstname","lastname","dateofb","email","address","phone")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=120, anchor="center")
        self.tree.pack(side="left", fill="both", expand=True)
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        # Pagination
        self.page = 1
        self.total = 0
        self.pager = PaginationBar(self.card, on_page_change=self._goto_page, page=self.page, total=self.total, page_size=PAGE_SIZE)
        self.pager.pack(anchor="e", pady=(6,0))

    def on_show(self):
        self._load()

    def _goto_page(self, page):
        self.page = page
        self._load()

    def _do_search(self, txt: str):
        self.page = 1
        self._load(txt)

    def _load(self, search: str = ""):
        def task(conn):
            return dao.list_persons(conn, search=search, page=self.page, page_size=PAGE_SIZE)
        def ok(res):
            rows, total = res
            self.total = total
            self._fill(rows)
            self.pager.total = self.total
            self.pager._build()
        self.controller.run_db_task(task, on_success=ok, on_error=self._err)

    def _fill(self, rows):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for r in rows:
            safe = list(r)
            safe[3] = safe[3].isoformat() if safe[3] else ""
            self.tree.insert("", "end", values=tuple(safe))

    def _on_select(self, _evt):
        it = self.tree.focus()
        if not it: return
        vals = self.tree.item(it, "values")
        keys = ["pid","firstname","lastname","dateofb","email","address","phone"]
        for k,v in zip(keys, vals):
            self.inputs[k].delete(0, tk.END)
            self.inputs[k].insert(0, v)

    def _create(self):
        try:
            pid = int(self.inputs["pid"].get())
            dob = date.fromisoformat(self.inputs["dateofb"].get())
            phone = int(self.inputs["phone"].get())
        except Exception as e:
            messagebox.showerror("שגיאה", f"קלט לא חוקי: {e}")
            return
        def task(conn):
            return dao.create_person(conn, pid,
                                     self.inputs["firstname"].get(),
                                     self.inputs["lastname"].get(),
                                     dob,
                                     self.inputs["email"].get(),
                                     self.inputs["address"].get(),
                                     phone)
        self.controller.run_db_task(task, on_success=lambda _: (messagebox.showinfo("הצלחה","נוצר"), self._load()), on_error=self._err)

    def _update(self):
        try:
            pid = int(self.inputs["pid"].get())
            dob = date.fromisoformat(self.inputs["dateofb"].get())
            phone = int(self.inputs["phone"].get())
        except Exception as e:
            messagebox.showerror("שגיאה", f"קלט לא חוקי: {e}")
            return
        def task(conn):
            return dao.update_person(conn, pid,
                                     self.inputs["firstname"].get(),
                                     self.inputs["lastname"].get(),
                                     dob,
                                     self.inputs["email"].get(),
                                     self.inputs["address"].get(),
                                     phone)
        self.controller.run_db_task(task, on_success=lambda _: (messagebox.showinfo("הצלחה","עודכן"), self._load()), on_error=self._err)

    def _delete(self):
        pid_txt = self.inputs["pid"].get().strip()
        if not pid_txt:
            return messagebox.showerror("שגיאה","PID חסר")
        if not messagebox.askyesno("אישור", f"בטוח למחוק PID {pid_txt}?"):
            return
        pid = int(pid_txt)
        def task(conn):
            return dao.delete_person(conn, pid)
        self.controller.run_db_task(task, on_success=lambda _: (messagebox.showinfo("הצלחה","נמחק"), self._load()), on_error=self._err)

    def _clear(self):
        for e in self.inputs.values():
            e.delete(0, tk.END)

    def _err(self, e):
        messagebox.showerror("שגיאה", str(e))
