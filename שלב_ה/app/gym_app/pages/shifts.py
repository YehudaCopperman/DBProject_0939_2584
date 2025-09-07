import tkinter as tk
from tkinter import ttk, messagebox, Toplevel
from datetime import datetime, date, time
from ..ui.base import BasePage
from ..ui.widgets import PaginationBar
from .. import dao
from ..config import PAGE_SIZE

# Table may hold TIME or TIMESTAMP from DB.
FMT_TS = "%Y-%m-%d %H:%M:%S"
TIME_HM = "%H:%M"
TIME_HMS = "%H:%M:%S"


class ShiftsPage(BasePage):
    """Shifts page with friendly time inputs (HH:MM). Hourly users are restricted to their PID."""

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
            ("PID", "pid"),                          # locked for hourly
            ("Shift Date (YYYY-MM-DD)", "date"),
            ("Clock In (HH:MM)", "clock_in_hm"),
            ("Clock Out (HH:MM)", "clock_out_hm"),
        ]
        for i, (lbl, k) in enumerate(fields):
            ttk.Label(form, text=lbl).grid(row=i, column=0, sticky="w", pady=4)
            ent = ttk.Entry(form, width=24)
            ent.grid(row=i, column=1, sticky="ew", pady=4, padx=(8, 0))
            self.inputs[k] = ent
        form.grid_columnconfigure(1, weight=1)

        ttk.Label(form, text="Tip: enter times like 08:30 or 17:00", style="SubTitle.TLabel")\
            .grid(row=len(fields), column=0, columnspan=2, sticky="w", pady=(2, 0))

        btns = ttk.Frame(form)
        btns.grid(row=len(fields) + 1, column=0, columnspan=2, sticky="e", pady=8)
        ttk.Button(btns, text="Create", style="Primary.TButton", command=self._create).pack(side="left", padx=4)
        ttk.Button(btns, text="Update", style="Ghost.TButton", command=self._update).pack(side="left", padx=4)
        ttk.Button(btns, text="Delete", style="Danger.TButton", command=self._delete).pack(side="left", padx=4)
        ttk.Button(btns, text="Clear", style="Ghost.TButton", command=self._clear).pack(side="left", padx=4)

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

        # Keep original selected values for WHERE clause
        self._current_selected = None  # (pid_str, date_str, old_clock_in_str)

    # ---------- role-aware setup ----------
    def on_show(self):
        role = (self.controller.current_user or {}).get("role")
        pid = (self.controller.current_user or {}).get("personid")

        if role == "hourly":
            self.inputs["pid"].configure(state="normal")
            self.inputs["pid"].delete(0, tk.END)
            if pid:
                self.inputs["pid"].insert(0, str(pid))
            self.inputs["pid"].configure(state="disabled")

            if not self.btn_change_pwd.winfo_ismapped():
                self.btn_change_pwd.pack(side="right")

            if self.filter_pid.winfo_ismapped():
                self.filter_pid.pack_forget()
            if self.lbl_filter_pid.winfo_ismapped():
                self.lbl_filter_pid.pack_forget()
        else:
            if self.btn_change_pwd.winfo_ismapped():
                self.btn_change_pwd.pack_forget()

            if not self.lbl_filter_pid.winfo_ismapped():
                self.lbl_filter_pid.pack(side="left", padx=(0, 6))
            if not self.filter_pid.winfo_ismapped():
                self.filter_pid.pack(side="left")

            self.inputs["pid"].configure(state="normal")

        self._load()

    # ---------- helpers ----------
    def _parse_hhmm(self, s: str) -> time:
        s = (s or "").strip()
        if not s:
            raise ValueError("Time is required (HH:MM)")
        # Try HH:MM, then HH:MM:SS
        try:
            return datetime.strptime(s, TIME_HM).time()
        except ValueError:
            return datetime.strptime(s, TIME_HMS).time()

    def _combine(self, d: date, hm: time) -> datetime:
        return datetime.combine(d, hm)

    def _parse_old_clock_in(self, sdate_s: str, cin_s: str) -> datetime | time:
        """
        Build the 'old_clock_in' value for the WHERE clause according to what the table gave us:
        - 'YYYY-MM-DD HH:MM:SS'  -> datetime
        - 'HH:MM:SS' or 'HH:MM'  -> time combined with sdate (if your column is TIME,
                                   passing a time or a timestamp is fine; PG will coerce)
        """
        cin_s = (cin_s or "").strip()
        if not cin_s:
            raise ValueError("Original clock_in missing")

        # Timestamp?
        try:
            return datetime.strptime(cin_s, FMT_TS)
        except ValueError:
            pass

        # TIME with seconds?
        try:
            t = datetime.strptime(cin_s, TIME_HMS).time()
            base_d = date.fromisoformat(sdate_s)
            # Return time if your column is TIME; returning datetime also works (PG casts),
            # but using time keeps types closer.
            return t
        except ValueError:
            pass

        # TIME HH:MM
        t = datetime.strptime(cin_s, TIME_HM).time()
        return t

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

        if role == "hourly":
            pid = user_pid
        else:
            f = self.filter_pid.get().strip()
            pid = int(f) if f.isdigit() else None

        m = self.filter_month.get().strip()
        y = self.filter_year.get().strip()
        month = int(m) if m.isdigit() and 1 <= int(m) <= 12 else None
        year = int(y) if y.isdigit() and len(y) == 4 else None

        def task(conn):
            return dao.list_shifts(conn, search_pid=pid, month=month, year=year,
                                   page=self.page, page_size=PAGE_SIZE)

        def ok(res):
            rows, total = res
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
        for pid, sdate, cin, cout in rows:
            # sdate may be date; cin/cout may be time or datetime
            sdate_s = sdate.isoformat() if isinstance(sdate, (date,)) else str(sdate or "")
            if isinstance(cin, datetime):
                cin_s = cin.strftime(FMT_TS)
            elif isinstance(cin, time):
                cin_s = cin.strftime(TIME_HMS)  # keep seconds for stable equality
            else:
                cin_s = str(cin or "")
            if isinstance(cout, datetime):
                cout_s = cout.strftime(FMT_TS)
            elif isinstance(cout, time):
                cout_s = cout.strftime(TIME_HMS)
            else:
                cout_s = str(cout or "")
            self.tree.insert("", "end", values=(pid, sdate_s, cin_s, cout_s))

    # ---------- CRUD handlers ----------
    def _on_select(self, _):
        it = self.tree.focus()
        if not it:
            return
        pid_s, sdate_s, cin_s, cout_s = self.tree.item(it, "values")

        # hourly cannot select others' rows
        role = (self.controller.current_user or {}).get("role")
        user_pid = (self.controller.current_user or {}).get("personid")
        if role == "hourly" and user_pid is not None and int(pid_s) != int(user_pid):
            return

        self._current_selected = (pid_s, sdate_s, cin_s)

        # Fill form
        for key, val in {"pid": pid_s, "date": sdate_s}.items():
            self.inputs[key].configure(state="normal")
            self.inputs[key].delete(0, tk.END)
            self.inputs[key].insert(0, val)

        # Convert table strings to HH:MM for inputs
        def to_hhmm(s: str) -> str:
            s = (s or "").strip()
            if not s:
                return ""
            for fmt in (TIME_HMS, FMT_TS, TIME_HM):
                try:
                    dt = datetime.strptime(s, fmt)
                    # if parsed as TIME (via TIME_HMS/TIME_HM), dt is datetime(1900...),
                    # so take its time() part via strftime.
                    return dt.strftime(TIME_HM)
                except ValueError:
                    continue
            # last resort: if it already looks like HH:MM:SS
            if len(s) == 8 and s.count(":") == 2:
                return s[:5]
            return s

        self.inputs["clock_in_hm"].delete(0, tk.END)
        self.inputs["clock_in_hm"].insert(0, to_hhmm(cin_s))
        self.inputs["clock_out_hm"].delete(0, tk.END)
        self.inputs["clock_out_hm"].insert(0, to_hhmm(cout_s))

        if role == "hourly":
            self.inputs["pid"].configure(state="disabled")

    def _create(self):
        role = (self.controller.current_user or {}).get("role")
        user_pid = (self.controller.current_user or {}).get("personid")
        try:
            pid = int(user_pid) if role == "hourly" else int(self.inputs["pid"].get())
            sdate = date.fromisoformat(self.inputs["date"].get())
            cin_hm = self._parse_hhmm(self.inputs["clock_in_hm"].get())
            cout_hm = self._parse_hhmm(self.inputs["clock_out_hm"].get())
            cin = self._combine(sdate, cin_hm)
            cout = self._combine(sdate, cout_hm)
            if cout <= cin:
                raise ValueError("Clock out must be after clock in.")
        except Exception as e:
            return messagebox.showerror("Error", f"Invalid input: {e}")

        def task(conn):
            return dao.create_shift(conn, pid, sdate, cin, cout)
        self.controller.run_db_task(task, on_success=lambda _:(messagebox.showinfo("Success","Created"), self._load()), on_error=self._err)

    def _update(self):
        if not self._current_selected:
            return messagebox.showerror("Error", "Select a shift to edit")

        role = (self.controller.current_user or {}).get("role")
        user_pid = (self.controller.current_user or {}).get("personid")
        try:
            pid = int(user_pid) if role == "hourly" else int(self.inputs["pid"].get())
            sdate_s = self.inputs["date"].get().strip()
            sdate = date.fromisoformat(sdate_s)
            new_cin_hm = self._parse_hhmm(self.inputs["clock_in_hm"].get())
            cout_hm = self._parse_hhmm(self.inputs["clock_out_hm"].get())
            new_cin = self._combine(sdate, new_cin_hm)
            cout = self._combine(sdate, cout_hm)
            if cout <= new_cin:
                raise ValueError("Clock out must be after clock in.")
            # exact old clock_in (time or timestamp) from selection
            _, sel_date, old_cin_s = self._current_selected
            old_cin = self._parse_old_clock_in(sel_date, old_cin_s)
        except Exception as e:
            return messagebox.showerror("Error", f"Invalid input: {e}")

        def task(conn):
            return dao.update_shift(conn, pid, sdate, old_cin, new_cin, cout)
        self.controller.run_db_task(task, on_success=lambda _:(messagebox.showinfo("Success","Updated"), self._load()), on_error=self._err)

    def _delete(self):
        if not self._current_selected:
            return messagebox.showerror("Error", "Select a shift to delete")

        role = (self.controller.current_user or {}).get("role")
        user_pid = (self.controller.current_user or {}).get("personid")
        pid_s, sdate_s, cin_s = self._current_selected
        pid = int(user_pid) if role == "hourly" else int(pid_s)

        if not messagebox.askyesno("Confirm", f"Delete shift for PID {pid} on {sdate_s}?"):
            return

        def task(conn):
            # pass cin_s as-is; PG can cast string to TIME/TIMESTAMP appropriately
            return dao.delete_shift(conn, pid, sdate_s, cin_s)
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

    def _err(self, e):
        messagebox.showerror("Error", str(e))
