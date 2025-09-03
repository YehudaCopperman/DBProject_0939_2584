from tkinter import ttk, messagebox
from ..ui.base import BasePage
from .. import dao


class LoginPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, "כניסה למערכת")

        frm = ttk.Frame(self.card, padding=20, style="Card.TFrame")
        frm.place(relx=0.5, rely=0.5, anchor="center")

        # --- התחברות רגילה (שם משתמש + סיסמה) ---
        ttk.Label(frm, text="שם משתמש").grid(row=0, column=0, sticky="w", pady=6)
        self.user = ttk.Entry(frm, width=28)
        self.user.grid(row=0, column=1, pady=6)

        ttk.Label(frm, text="סיסמה").grid(row=1, column=0, sticky="w", pady=6)
        self.pw = ttk.Entry(frm, show="*", width=28)
        self.pw.grid(row=1, column=1, pady=6)

        ttk.Button(
            frm, text="התחבר", style="Primary.TButton", command=self._login
        ).grid(row=2, column=0, columnspan=2, pady=12)

        # נוחות: Enter מקדם שדות/מאמת
        self.user.bind("<Return>", lambda e: self.pw.focus_set())
        self.pw.bind("<Return>", lambda e: self._login())

        # --- כניסת עובד שעתי לפי ת״ז (ללא סיסמה) ---
        ttk.Label(frm, text="ת״ז עובד שעתי").grid(row=3, column=0, sticky="w", pady=(16, 6))
        self.pid_entry = ttk.Entry(frm, width=28)
        self.pid_entry.grid(row=3, column=1, pady=(16, 6))

        ttk.Button(
            frm,
            text="כניסת עובד שעתי לפי ת״ז",
            style="Ghost.TButton",
            command=self._login_hourly_by_pid,
        ).grid(row=4, column=0, columnspan=2, pady=6)

        self.pid_entry.bind("<Return>", lambda e: self._login_hourly_by_pid())

    # -------------------- התחברות רגילה (username/password) --------------------
    def _login(self):
        username = self.user.get().strip()
        password = self.pw.get()

        if not username or not password:
            messagebox.showerror("שגיאה", "יש למלא שם משתמש וסיסמה")
            return

        def task(conn):
            return dao.authenticate_user(conn, username, password)

        def ok(row):
            if not row:
                messagebox.showerror("שגיאה", "פרטי ההתחברות שגויים")
                return

            user_id, personid, role = row
            # שומרים פרטי משתמש באפליקציה הראשית
            self.controller.current_user = {
                "user_id": user_id,
                "username": username,
                "personid": personid,
                "role": role,
            }
            messagebox.showinfo("ברוך הבא", f"התחברת כ־{role}")

            # ניווט לפי תפקיד
            if role == "admin":
                self.controller.show_frame("DashboardPage")
            elif role == "hourly":
                self.controller.show_frame("ShiftsPage")
            else:
                messagebox.showerror("שגיאה", "אין לך הרשאה (denied)")

        self.controller.run_db_task(
            task,
            on_success=ok,
            on_error=lambda e: messagebox.showerror("DB Error", str(e)),
        )

    # -------------------- כניסת עובד שעתי לפי ת״ז בלבד --------------------
    def _login_hourly_by_pid(self):
        pid_str = (self.pid_entry.get() or "").strip()
        if not pid_str.isdigit():
            messagebox.showerror("שגיאה", "יש להזין ת״ז ספרתית (PID)")
            return
        pid = int(pid_str)

        def task(conn):
            return dao.is_hourly_pid(conn, pid)

        def ok(is_hourly: bool):
            if not is_hourly:
                messagebox.showerror("שגיאה", f"ת״ז {pid} אינה משויכת לעובד שעתי")
                return

            # קובע משתמש נוכחי ומנווט למשמרות
            self.controller.current_user = {
                "user_id": None,
                "username": f"pid:{pid}",
                "personid": pid,
                "role": "hourly",
            }
            messagebox.showinfo("ברוך הבא", f"התחברת כ־hourly (PID {pid})")
            self.controller.show_frame("ShiftsPage")

        self.controller.run_db_task(
            task,
            on_success=ok,
            on_error=lambda e: messagebox.showerror("DB Error", str(e)),
        )
