from tkinter import ttk, messagebox
from ..ui.base import BasePage
from .. import dao


class DashboardPage(BasePage):
    """
    Admin landing page with navigation shortcuts and admin tools.

    - Navigation:
        Persons, Members, Shifts, Reports, Data Manager, Logout
    - Admin Tools (visible only when role == 'admin'):
        Reset an hourly user's credentials to defaults:
        username = PID, password = PID.
    """

    def __init__(self, parent, controller):
        super().__init__(parent, controller, "Dashboard")

        # Top navigation
        nav = ttk.Frame(self.card, padding=12, style="Card.TFrame")
        nav.pack(fill="x", pady=8)

        ttk.Button(
            nav, text="Persons", style="Nav.TButton",
            command=lambda: controller.show_frame("PersonsPage")
        ).pack(anchor="w", pady=4)

        ttk.Button(
            nav, text="Members", style="Nav.TButton",
            command=lambda: controller.show_frame("MembersPage")
        ).pack(anchor="w", pady=4)

        ttk.Button(
            nav, text="Shifts", style="Nav.TButton",
            command=lambda: controller.show_frame("ShiftsPage")
        ).pack(anchor="w", pady=4)

        ttk.Button(
            nav, text="Reports", style="Nav.TButton",
            command=lambda: controller.show_frame("ReportsPage")
        ).pack(anchor="w", pady=4)

        # NEW: Data Manager (generic CRUD for whitelisted tables)
        ttk.Button(
            nav, text="Data Manager", style="Nav.TButton",
            command=lambda: controller.show_frame("DataManagerPage")
        ).pack(anchor="w", pady=4)

        # Logout (back to Login screen)
        ttk.Button(
            nav, text="Logout", style="Ghost.TButton",
            command=self._logout
        ).pack(anchor="w", pady=(12, 0))

        # Admin-only tools (shown only if role == 'admin')
        self.admin_frame = ttk.LabelFrame(self.card, text="Admin Tools", padding=12)
        self.admin_frame.pack(fill="x", pady=(16, 8))

        ttk.Label(
            self.admin_frame,
            text="Reset hourly user's credentials to defaults (username & password = PID)"
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 6))

        ttk.Label(self.admin_frame, text="PID").grid(row=1, column=0, sticky="w")
        self.reset_pid = ttk.Entry(self.admin_frame, width=18)
        self.reset_pid.grid(row=1, column=1, sticky="w", padx=(8, 0))

        ttk.Button(
            self.admin_frame, text="Reset password to default", style="Danger.TButton",
            command=self._admin_reset_pwd
        ).grid(row=2, column=0, columnspan=2, sticky="e", pady=8)

    # ---------- lifecycle ----------
    def on_show(self):
        """Show/hide admin tools based on the current user's role."""
        role = (self.controller.current_user or {}).get("role")
        if role == "admin":
            if not self.admin_frame.winfo_ismapped():
                self.admin_frame.pack(fill="x", pady=(16, 8))
        else:
            if self.admin_frame.winfo_ismapped():
                self.admin_frame.pack_forget()

    # ---------- actions ----------
    def _admin_reset_pwd(self):
        """Reset the given PID's credentials to defaults (username = PID, password = PID)."""
        pid_s = (self.reset_pid.get() or "").strip()
        if not pid_s.isdigit():
            return messagebox.showerror("Error", "PID must be numeric")
        pid = int(pid_s)

        def task(conn):
            dao.admin_reset_password_by_pid(conn, pid)

        def ok(_=None):
            messagebox.showinfo(
                "Done",
                f"Credentials reset.\nUsername = {pid}\nPassword = {pid}"
            )

        self.controller.run_db_task(
            task,
            on_success=ok,
            on_error=lambda e: messagebox.showerror("DB Error", str(e)),
        )

    def _logout(self):
        """Clear session and navigate back to Login page."""
        self.controller.current_user = {
            "user_id": None,
            "username": None,
            "personid": None,
            "role": None,
        }
        self.controller.show_frame("LoginPage")
