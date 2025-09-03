
# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
from ..ui.base import BasePage
from ..ui.widgets import SearchBar, PaginationBar
from .. import dao
from ..config import PAGE_SIZE

class MembersPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, "ניהול חברים (Member)")
        top = ttk.Frame(self.card, style="Card.TFrame")
        top.pack(fill="x")
        self.search_bar = SearchBar(top, on_search=self._do_search, placeholder="חפש לפי שם...")
        self.search_bar.pack(side="left")
        ttk.Button(top, text="רענן", style="Ghost.TButton", command=lambda: self._load()).pack(side="right")

        form = ttk.LabelFrame(self.card, text="פרטי חבר", padding=12)
        form.pack(fill="x", pady=8)
        self.inputs = {}
        fields = [
            ("PID (PersonID)","pid"),
            ("שם פרטי","firstname"),
            ("שם משפחה","lastname"),
            ("תאריך לידה YYYY-MM-DD","dateofb"),
            ("Email","email"),
            ("כתובת","address"),
            ("טלפון","phone"),
            ("סוג חברות","membershiptype"),
            ("פעיל? (true/false)","isactive"),
        ]
        for i,(label,key) in enumerate(fields):
            ttk.Label(form, text=label).grid(row=i, column=0, sticky="w", pady=4)
            ent = ttk.Entry(form, width=32)
            ent.grid(row=i, column=1, sticky="ew", pady=4, padx=(8,0))
            self.inputs[key]=ent
        form.grid_columnconfigure(1, weight=1)
        btns = ttk.Frame(form)
        btns.grid(row=len(fields), column=0, columnspan=2, sticky="e", pady=(8,0))
        ttk.Button(btns, text="Upsert (פרוצדורה)", style="Primary.TButton", command=self._upsert_proc).pack(side="left", padx=4)
        ttk.Button(btns, text="עדכן", style="Ghost.TButton", command=self._update_member).pack(side="left", padx=4)
        ttk.Button(btns, text="מחק", style="Danger.TButton", command=self._delete_member).pack(side="left", padx=4)
        ttk.Button(btns, text="נקה", style="Ghost.TButton", command=self._clear).pack(side="left", padx=4)

        table_frame = ttk.Frame(self.card, padding=(0,8,0,0), style="Card.TFrame")
        table_frame.pack(fill="both", expand=True)
        cols = ("pid","firstname","lastname","membershiptype","memberstartdate","isactive")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=140, anchor="center")
        self.tree.pack(side="left", fill="both", expand=True)
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        self.page = 1
        self.total = 0
        self.pager = PaginationBar(self.card, on_page_change=self._goto_page, page=self.page, total=self.total, page_size=PAGE_SIZE)
        self.pager.pack(anchor="e", pady=(6,0))

    def on_show(self):
        self._load()

    def _goto_page(self, page): self.page = page; self._load()
    def _do_search(self, txt): self.page = 1; self._load(txt)

    def _load(self, search: str = ""):
        def task(conn):
            return dao.list_members(conn, search=search, page=self.page, page_size=PAGE_SIZE)
        def ok(res):
            rows, total = res
            self.total = total
            self._fill(rows)
            self.pager.total = self.total
            self.pager._build()
        self.controller.run_db_task(task, on_success=ok, on_error=self._err)

    def _fill(self, rows):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for r in rows:
            safe = list(r)
            safe[4] = safe[4].isoformat() if safe[4] else ""
            safe[5] = "True" if safe[5] else "False"
            self.tree.insert("", "end", values=tuple(safe))

    def _on_select(self, _evt):
        it = self.tree.focus()
        if not it: return
        pid, fn, ln, mtype, start, active = self.tree.item(it, "values")
        for k,v in {
            "pid": pid, "firstname": fn, "lastname": ln, "membershiptype": mtype,
        }.items():
            self.inputs[k].delete(0, tk.END); self.inputs[k].insert(0, v)

    def _upsert_proc(self):
        try:
            pid = int(self.inputs["pid"].get())
            dob = date.fromisoformat(self.inputs["dateofb"].get()) if self.inputs["dateofb"].get() else None
            phone = int(self.inputs["phone"].get()) if self.inputs["phone"].get() else None
            isactive = self.inputs["isactive"].get().strip().lower() in ("true","1","yes","y","t")
        except Exception as e:
            return messagebox.showerror("שגיאה", f"קלט שגוי: {e}")

        def task(conn):
            return dao.upsert_member_via_proc(conn, pid,
                                              self.inputs["firstname"].get(),
                                              self.inputs["lastname"].get(),
                                              dob,
                                              self.inputs["email"].get(),
                                              self.inputs["address"].get(),
                                              phone,
                                              self.inputs["membershiptype"].get(),
                                              isactive)
        self.controller.run_db_task(task, on_success=lambda _: (messagebox.showinfo("הצלחה","בוצע"), self._load()), on_error=self._err)

    def _update_member(self):
        try:
            pid = int(self.inputs["pid"].get())
            isactive = self.inputs["isactive"].get().strip().lower() in ("true","1","yes","y","t")
        except Exception as e:
            return messagebox.showerror("שגיאה", f"קלט שגוי: {e}")
        def task(conn):
            return dao.update_member(conn, pid, self.inputs["membershiptype"].get(), isactive)
        self.controller.run_db_task(task, on_success=lambda _: (messagebox.showinfo("הצלחה","עודכן"), self._load()), on_error=self._err)

    def _delete_member(self):
        pid_txt = self.inputs["pid"].get().strip()
        if not pid_txt: return messagebox.showerror("שגיאה","PID חסר")
        if not messagebox.askyesno("אישור", f"בטוח למחוק חברות ל-PID {pid_txt}?"): return
        def task(conn):
            return dao.delete_member(conn, int(pid_txt))
        self.controller.run_db_task(task, on_success=lambda _: (messagebox.showinfo("הצלחה","נמחק"), self._load()), on_error=self._err)

    def _clear(self):
        for e in self.inputs.values():
            e.delete(0, tk.END)

    def _err(self, e): messagebox.showerror("שגיאה", str(e))
