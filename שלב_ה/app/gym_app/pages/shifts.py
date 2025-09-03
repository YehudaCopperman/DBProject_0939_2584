import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date
from ..ui.base import BasePage
from ..ui.widgets import PaginationBar
from .. import dao
from ..config import PAGE_SIZE

FMT_TS = "%Y-%m-%d %H:%M:%S"

class ShiftsPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, "משמרות (Shift)")

        # --- טופס עריכה ---
        form = ttk.LabelFrame(self.card, text="ניהול משמרת", padding=12)
        form.pack(fill="x", pady=8)

        self.inputs = {}
        fields = [
            ("PID", "pid"),  # אצל hourly יינעל לערך שלו
            ("תאריך משמרת YYYY-MM-DD", "date"),
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
        ttk.Button(btns, text="הוסף", style="Primary.TButton", command=self._create).pack(side="left", padx=4)
        ttk.Button(btns, text="עדכן", style="Ghost.TButton", command=self._update).pack(side="left", padx=4)
        ttk.Button(btns, text="מחק", style="Danger.TButton", command=self._delete).pack(side="left", padx=4)
        ttk.Button(btns, text="נקה", style="Ghost.TButton", command=self._clear).pack(side="left", padx=4)

        # --- פס סינון ---
        filt = ttk.Frame(self.card, padding=(0, 6, 0, 0), style="Card.TFrame")
        filt.pack(fill="x")

        # נשמור רפרנס גם לתווית כדי שנוכל להסתיר אותה
        self.lbl_filter_pid = ttk.Label(filt, text="סינון לפי PID")
        self.lbl_filter_pid.pack(side="left", padx=(0, 6))
        self.filter_pid = ttk.Entry(filt, width=10)
        self.filter_pid.pack(side="left")

        ttk.Label(filt, text="חודש (1-12)").pack(side="left", padx=(12, 6))
        self.filter_month = ttk.Entry(filt, width=6)
        self.filter_month.pack(side="left")

        ttk.Label(filt, text="שנה (YYYY)").pack(side="left", padx=(12, 6))
        self.filter_year = ttk.Entry(filt, width=8)
        self.filter_year.pack(side="left")

        ttk.Button(filt, text="סנן", style="Ghost.TButton", command=self._apply_filter).pack(side="left", padx=6)
        ttk.Button(filt, text="נקה סינון", style="Ghost.TButton", command=self._clear_filter).pack(side="left")

        # --- טבלה ---
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

        # --- פאג'ינציה ---
        self.page = 1
        self.total = 0
        self.pager = PaginationBar(self.card, on_page_change=self._goto_page,
                                   page=self.page, total=self.total, page_size=PAGE_SIZE)
        self.pager.pack(anchor="e", pady=6)

        self._current_selected = None

    def on_show(self):
        role = (self.controller.current_user or {}).get("role")
        pid = (self.controller.current_user or {}).get("personid")

        if role == "hourly":
            # נעל PID בטופס
            self.inputs["pid"].configure(state="normal")
            self.inputs["pid"].delete(0, tk.END)
            if pid:
                self.inputs["pid"].insert(0, str(pid))
            self.inputs["pid"].configure(state="disabled")

            # הסתרת סינון PID לחלוטין
            if self.filter_pid.winfo_ismapped():
                self.filter_pid.pack_forget()
            if self.lbl_filter_pid.winfo_ismapped():
                self.lbl_filter_pid.pack_forget()
        else:
            # אדמין
            if not self.lbl_filter_pid.winfo_ismapped():
                self.lbl_filter_pid.pack(side="left", padx=(0,6))
            if not self.filter_pid.winfo_ismapped():
                self.filter_pid.pack(side="left")

            self.inputs["pid"].configure(state="normal")

        self._load()

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

    def _load(self):
        role = (self.controller.current_user or {}).get("role")
        user_pid = (self.controller.current_user or {}).get("personid")

        # מי ה-PID לבקשה?
        if role == "hourly":
            pid = user_pid
        else:
            f = self.filter_pid.get().strip()
            pid = int(f) if f.isdigit() else None

        # month/year
        m = self.filter_month.get().strip()
        y = self.filter_year.get().strip()
        month = int(m) if m.isdigit() and 1 <= int(m) <= 12 else None
        year  = int(y) if y.isdigit() and len(y) == 4 else None

        def task(conn):
            return dao.list_shifts(conn, search_pid=pid, month=month, year=year,
                                   page=self.page, page_size=PAGE_SIZE)

        def ok(res):
            rows, total = res

            # הגנה נוספת בצד־לקוח: אם hourly, נציג רק את השורות של עצמו, גם אם בטעות השרת החזיר אחרות.
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

    def _on_select(self, _):
        it = self.tree.focus()
        if not it:
            return
        pid, sdate, cin, cout = self.tree.item(it, "values")

        # אם hourly בחר שורה לא שלו — נתעלם
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
            return messagebox.showerror("שגיאה", f"קלט שגוי: {e}")

        def task(conn):
            return dao.create_shift(conn, pid, sdate, cin, cout)
        self.controller.run_db_task(task, on_success=lambda _:(messagebox.showinfo("הצלחה","נוצר"), self._load()), on_error=self._err)

    def _update(self):
        if not self._current_selected:
            return messagebox.showerror("שגיאה", "בחר משמרת לעריכה")

        role = (self.controller.current_user or {}).get("role")
        user_pid = (self.controller.current_user or {}).get("personid")
        try:
            pid = int(user_pid) if role == "hourly" else int(self.inputs["pid"].get())
            sdate = date.fromisoformat(self.inputs["date"].get())
            new_cin = datetime.strptime(self.inputs["clock_in"].get(), FMT_TS)
            cout = datetime.strptime(self.inputs["clock_out"].get(), FMT_TS)
            old_cin = datetime.strptime(self._current_selected[2], FMT_TS)
        except Exception as e:
            return messagebox.showerror("שגיאה", f"קלט שגוי: {e}")

        def task(conn):
            return dao.update_shift(conn, pid, sdate, old_cin, new_cin, cout)
        self.controller.run_db_task(task, on_success=lambda _:(messagebox.showinfo("הצלחה","עודכן"), self._load()), on_error=self._err)

    def _delete(self):
        if not self._current_selected:
            return messagebox.showerror("שגיאה", "בחר משמרת למחיקה")

        role = (self.controller.current_user or {}).get("role")
        user_pid = (self.controller.current_user or {}).get("personid")
        pid, sdate, cin = self._current_selected
        pid = int(user_pid) if role == "hourly" else int(pid)

        if not messagebox.askyesno("אישור", f"למחוק משמרת של PID {pid} בתאריך {sdate}?"):
            return

        def task(conn):
            return dao.delete_shift(conn, pid, sdate, cin)
        self.controller.run_db_task(task, on_success=lambda _:(messagebox.showinfo("הצלחה","נמחק"), self._load()), on_error=self._err)

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
        messagebox.showerror("שגיאה", str(e))
