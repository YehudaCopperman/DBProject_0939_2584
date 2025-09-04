import tkinter as tk
from tkinter import ttk, messagebox, Toplevel
from datetime import datetime, date
from ..ui.base import BasePage
from ..ui.widgets import PaginationBar
from .. import dao
from ..config import PAGE_SIZE

FMT_TS = "%Y-%m-%d %H:%M:%S"

class ShiftsPage(BasePage):
    """Shifts page: 
    - hourly users: view their own shifts, can CREATE only (no update/delete) + change own password
    - admin: full CRUD and filters
    """

    def __init__(self, parent, controller):
        super().__init__(parent, controller, "Shifts")

        # --- header actions (role-specific) ---
        self.actions_bar = ttk.Frame(self.card, padding=(0, 6, 0, 0), style="Card.TFrame")
        self.actions_bar.pack(fill="x")
        # Visible only for hourly users:
        self.btn_change_pwd = ttk.Button(
            self.actions_bar, text="Change Password", style="Ghost.TButton",
            command=self._open_change_password_dialog
        )

        # --- edit form ---
        form = ttk.LabelFrame(self.card, text="Shift Editor", padding=12)
        form.pack(fill="x", pady=8)

        self.inputs = {}
        fields = [
            ("PID", "pid"),  # locked for hourly role
            ("Shift Date YYYY-MM-DD", "date"),
            ("Clock In YYYY-MM-DD HH:MM:SS", "clock_in"),
            ("Clock Out YYYY-MM-DD HH:MM:SS", "clock_out"),
        ]
        for i, (lbl, k) in enumerate(fields):
            ttk.Label(form, text=lbl).grid(row=i, column=0, sticky="w", pady=4)
            ent = ttk.Entry(form, width=32)
            ent.grid(row=i, column=1, sticky="ew", pady=4, padx=(8, 0))
            self.inputs[k] = ent
        form.grid_columnconfigure(1, weight=1)

        btns = ttk.Frame(form)
        btns.grid(row=len(fields), column=0, columnspan=2, sticky="e", pady=8)
        # keep references so we can show/hide by role
        self.btn_create = ttk.Button(btns, text="Create", style="Primary.TButton", command=self._create)
        self.btn_update = ttk.Button(btns, text="Update", style="Ghost.TButton", command=self._update)
        self.btn_delete = ttk.Button(btns, text="Delete", style="Danger.TButton", command=self._delete)
        self.btn_clear  = ttk.Button(btns, text="Clear",  style="Ghost.TButton", command=self._clear)

        self.btn_create.pack(side="left", padx=4)
        self.btn_update.pack(side="left", padx=4)
        self.btn_delete.pack(side="left", padx=4)
        self.btn_clear.pack(side="left", padx=4)

        # --- filter bar ---
        filt = ttk.Frame(self.card, padding=(0, 6, 0, 0), style="Card.TFrame")
        filt.pack(fill="x")
        self.lbl_filter_pid = ttk.Label(filt, text="Filter by PID")
        self.lbl_filter_pid.pack(side="left", padx=(0, 6))
        self.filter_pid = ttk.Entry(filt, width=10)
        self.filter_pid.pack(side="left")

        ttk.Label(filt, text="Month (1-12)").pack(side="left", padx=(12, 6))
        self.filter_month = ttk.Entry(filt, width=6)
        self.filter_month.pack(side="left")

        ttk.Label(filt, text="Year (YYYY)").pack(side="left", padx=(12, 6))
        self.filter_year = ttk.Entry(filt, width=8)
        self.filter_year.pack(side="left")

        ttk.Button(filt, text="Apply", style="Ghost.TButton", command=self._apply_filter).pack(side="left", padx=6)
        ttk.Button(filt, text="Clear Filters", style="Ghost.TButton", command=self._clear_filter).pack(side="left")

        # --- table ---
        table = ttk.Frame(self.card, padding=(0, 8, 0, 0), style="Card.TFrame")
        table.pack(fill="both", expand=True)
        cols = ("pid", "date", "clock_in", "clock_out")
        self.tree = ttk.Treeview(table, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=160, anchor="center")
        self.tree.pack(side="left", fill="both", expand=True)
        vsb = ttk.Scrollbar(table, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        # --- pagination ---
        self.page = 1
        self.total = 0
        self.pager = PaginationBar(self.card, on_page_change=self._goto_page,
                                   page=self.page, total=self.total, page_size=PAGE_SIZE)
        self.pager.pack(anchor="e", pady=6)

        self._current_selected = None

    # ---------- role-aware setup ----------
    def on_show(self):
        role = (self.controller.current_user or {}).get("role")
        pid = (self.controller.current_user or {}).get("personid")

        # Hourly: lock PID in form, show change password button, hide admin filters & update/delete
        if role == "hourly":
            # lock PID field
            self.inputs["pid"].configure(state="normal")
            self.inputs["pid"].delete(0, tk.END)
            if pid:
                self.inputs["pid"].insert(0, str(pid))
            self.inputs["pid"].configure(state="disabled")

            # show change password button
            if not self.btn_change_pwd.winfo_ismapped():
                self.btn_change_pwd.pack(side="right")

            # hide PID filter widgets
            if self.filter_pid.winfo_ismapped():
                self.filter_pid.pack_forget()
            if self.lbl_filter_pid.winfo_ismapped():
                self.lbl_filter_pid.pack_forget()

            # hide Update/Delete for hourly
            if self.btn_update.winfo_ismapped():
                self.btn_update.pack_forget()
            if self.btn_delete.winfo_ismapped():
                self.btn_delete.pack_forget()
            # show Create/Clear (ensure they are visible)
            if not self.btn_create.winfo_ismapped():
                self.btn_create.pack(side="left", padx=4)
            if not self.btn_clear.winfo_ismapped():
                self.btn_clear.pack(side="left", padx=4)

        else:
            # Admin: allow PID editing, show all filters and all buttons, hide change-pwd quick action
            if self.btn_change_pwd.winfo_ismapped():
                self.btn_change_pwd.pack_forget()

            if not self.lbl_filter_pid.winfo_ismapped():
                self.lbl_filter_pid.pack(side="left", padx=(0, 6))
            if not self.filter_pid.winfo_ismapped():
                self.filter_pid.pack(side="left")

            self.inputs["pid"].configure(state="normal")

            # ensure all CRUD buttons are visible
            if not self.btn_update.winfo_ismapped():
                self.btn_update.pack(side="left", padx=4)
            if not self.btn_delete.winfo_ismapped():
                self.btn_delete.pack(side="left", padx=4)
            if not self.btn_create.winfo_ismapped():
                self.btn_create.pack(side="left", padx=4)
            if not self.btn_clear.winfo_ismapped():
                self.btn_clear.pack(side="left", padx=4)

        self._load()

    # ---------- change password dialog (hourly only) ----------
    def _open_change_password_dialog(self):
        role = (self.controller.current_user or {}).get("role")
        pid = (self.controller.current_user or {}).get("personid")
        if role != "hourly" or pid is None:
            return

        dlg = Toplevel(self)
        dlg.title("Change Password")
        dlg.transient(self.winfo_toplevel())
        dlg.grab_set()

        frm = ttk.Frame(dlg, padding=16)
        frm.pack(fill="both", expand=True)

        ttk.Label(frm, text=f"PID: {pid}").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))

        ttk.Label(frm, text="Current password").grid(row=1, column=0, sticky="w", pady=4)
        e_old = ttk.Entry(frm, show="*", width=28)
        e_old.grid(row=1, column=1, pady=4)

        ttk.Label(frm, text="New password").grid(row=2, column=0, sticky="w", pady=4)
        e_new = ttk.Entry(frm, show="*", width=28)
        e_new.grid(row=2, column=1, pady=4)

        btns = ttk.Frame(frm)
        btns.grid(row=3, column=0, columnspan=2, sticky="e", pady=(10, 0))
        ttk.Button(btns, text="Cancel", style="Ghost.TButton", command=dlg.destroy).pack(side="left", padx=4)

        def submit():
            old = (e_old.get() or "").strip()
            new = (e_new.get() or "").strip()
            if not old or not new:
                return messagebox.showerror("Error", "Both fields are required", parent=dlg)
            if len(new) < 4:
                return messagebox.showerror("Error", "New password must be at least 4 characters", parent=dlg)

            def task(conn):
                return dao.change_password_by_pid(conn, int(pid), old, new)

            def ok(changed: bool):
                if not changed:
                    return messagebox.showerror("Error", "Wrong current password or operation failed", parent=dlg)
                messagebox.showinfo("Success", "Password changed successfully", parent=dlg)
                dlg.destroy()

            self.controller.run_db_task(
                task, on_success=ok, on_error=lambda e: messagebox.showerror("DB Error", str(e), parent=dlg)
            )

        ttk.Button(btns, text="Change", style="Primary.TButton", command=submit).pack(side="left", padx=4)
        e_old.bind("<Return>", lambda _: e_new.focus_set())
        e_new.bind("<Return>", lambda _: submit())
        e_old.focus_set()

    # ---------- pagination & filters ----------
    def _goto_page(self, p):
        self.page = p
        self._load()

    def _apply_filter(self):
        self.page = 1
        self._load()

    def _clear_filter(self):
        self.filter_month.delete(0, tk.END)
        self.filter_year.delete(0, tk.END)
        if self.controller.current_user.get("role") == "admin":
            self.filter_pid.delete(0, tk.END)
        self._load()

    # ---------- data loading ----------
    def _load(self):
        role = (self.controller.current_user or {}).get("role")
        user_pid = (self.controller.current_user or {}).get("personid")

        # determine PID filter
        if role == "hourly":
            pid = user_pid
        else:
            f = self.filter_pid.get().strip()
            pid = int(f) if f.isdigit() else None

        # month/year
        m = self.filter_month.get().strip()
        y = self.filter_year.get().strip()
        month = int(m) if m.isdigit() and 1 <= int(m) <= 12 else None
        year = int(y) if y.isdigit() and len(y) == 4 else None

        def task(conn):
            return dao.list_shifts(conn, search_pid=pid, month=month, year=year,
                                   page=self.page, page_size=PAGE_SIZE)

        def ok(res):
            rows, total = res

            # extra client-side guard for hourly
            if role == "hourly" and user_pid is not None:
                rows = [r for r in rows if int(r[0]) == int(user_pid)]
                total = len(rows)

            self.total = total
            self._fill(rows)
            self.pager.total = total
            self.pager._build()

        self.controller.run_db_task(task, on_success=ok, on_error=self._err)

    def _fill(self, rows):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for r in rows:
            pid, sdate, cin, cout = r
            sdate = sdate.isoformat() if sdate else ""
            cin = cin.strftime(FMT_TS) if cin else ""
            cout = cout.strftime(FMT_TS) if cout else ""
            self.tree.insert("", "end", values=(pid, sdate, cin, cout))

    # ---------- CRUD handlers ----------
    def _on_select(self, _):
        it = self.tree.focus()
        if not it:
            return
        pid, sdate, cin, cout = self.tree.item(it, "values")

        # hourly cannot select others' rows
        role = (self.controller.current_user or {}).get("role")
        user_pid = (self.controller.current_user or {}).get("personid")
        if role == "hourly" and user_pid is not None and int(pid) != int(user_pid):
            return

        self._current_selected = (pid, sdate, cin)
        for key, val in {"pid": pid, "date": sdate, "clock_in": cin, "clock_out": cout}.items():
            self.inputs[key].configure(state="normal")
            self.inputs[key].delete(0, tk.END)
            self.inputs[key].insert(0, val)
        if role == "hourly":
            self.inputs["pid"].configure(state="disabled")

    def _create(self):
        role = (self.controller.current_user or {}).get("role")
        user_pid = (self.controller.current_user or {}).get("personid")
        try:
            pid = int(user_pid) if role == "hourly" else int(self.inputs["pid"].get())
            sdate = date.fromisoformat(self.inputs["date"].get())
            cin = datetime.strptime(self.inputs["clock_in"].get(), FMT_TS)
            cout = datetime.strptime(self.inputs["clock_out"].get(), FMT_TS)
        except Exception as e:
            return messagebox.showerror("Error", f"Invalid input: {e}")

        def task(conn):
            return dao.create_shift(conn, pid, sdate, cin, cout)
        self.controller.run_db_task(task, on_success=lambda _:(messagebox.showinfo("Success","Created"), self._load()), on_error=self._err)

    def _update(self):
        # hard guard: hourly not allowed
        if (self.controller.current_user or {}).get("role") == "hourly":
            return messagebox.showerror("Access", "Hourly workers cannot update shifts.")
        if not self._current_selected:
            return messagebox.showerror("Error", "Select a shift to edit")

        try:
            pid = int(self.inputs["pid"].get())
            sdate = date.fromisoformat(self.inputs["date"].get())
            new_cin = datetime.strptime(self.inputs["clock_in"].get(), FMT_TS)
            cout = datetime.strptime(self.inputs["clock_out"].get(), FMT_TS)
            old_cin = datetime.strptime(self._current_selected[2], FMT_TS)
        except Exception as e:
            return messagebox.showerror("Error", f"Invalid input: {e}")

        def task(conn):
            return dao.update_shift(conn, pid, sdate, old_cin, new_cin, cout)
        self.controller.run_db_task(task, on_success=lambda _:(messagebox.showinfo("Success","Updated"), self._load()), on_error=self._err)

    def _delete(self):
        # hard guard: hourly not allowed
        if (self.controller.current_user or {}).get("role") == "hourly":
            return messagebox.showerror("Access", "Hourly workers cannot delete shifts.")
        if not self._current_selected:
            return messagebox.showerror("Error", "Select a shift to delete")

        pid, sdate, cin = self._current_selected
        if not messagebox.askyesno("Confirm", f"Delete shift for PID {pid} on {sdate}?"):
            return

        def task(conn):
            return dao.delete_shift(conn, int(pid), sdate, cin)
        self.controller.run_db_task(task, on_success=lambda _:(messagebox.showinfo("Success","Deleted"), self._load()), on_error=self._err)

    def _clear(self):
        for e in self.inputs.values():
            e.configure(state="normal")
            e.delete(0, tk.END)
        self._current_selected = None
        if (self.controller.current_user or {}).get("role") == "hourly":
            pid = self.controller.current_user.get("personid")
            self.inputs["pid"].insert(0, str(pid))
            self.inputs["pid"].configure(state="disabled")

    def _err(self, e):
        messagebox.showerror("Error", str(e))
