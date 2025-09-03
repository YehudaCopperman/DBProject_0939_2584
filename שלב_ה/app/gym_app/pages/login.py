from tkinter import ttk, messagebox
from ..ui.base import BasePage
from .. import dao


class LoginPage(BasePage):
    """Login screen with standard credentials only (username + password)."""

    def __init__(self, parent, controller):
        super().__init__(parent, controller, "Login")

        frm = ttk.Frame(self.card, padding=20, style="Card.TFrame")
        frm.place(relx=0.5, rely=0.5, anchor="center")

        # --- standard login (username + password) ---
        ttk.Label(frm, text="Username").grid(row=0, column=0, sticky="w", pady=6)
        self.user = ttk.Entry(frm, width=28)
        self.user.grid(row=0, column=1, pady=6)

        ttk.Label(frm, text="Password").grid(row=1, column=0, sticky="w", pady=6)
        self.pw = ttk.Entry(frm, show="*", width=28)
        self.pw.grid(row=1, column=1, pady=6)

        ttk.Button(
            frm, text="Log in", style="Primary.TButton", command=self._login
        ).grid(row=2, column=0, columnspan=2, pady=12)

        # convenience: Enter key navigation
        self.user.bind("<Return>", lambda e: self.pw.focus_set())
        self.pw.bind("<Return>", lambda e: self._login())

    # -------------------- standard login --------------------
    def _login(self):
        username = (self.user.get() or "").strip()
        password = self.pw.get()

        if not username or not password:
            messagebox.showerror("Error", "Username and password are required")
            return

        def task(conn):
            return dao.authenticate_user(conn, username, password)

        def ok(row):
            if not row:
                messagebox.showerror("Error", "Invalid credentials")
                return

            user_id, personid, role = row
            # update in-memory session
            self.controller.current_user = {
                "user_id": user_id,
                "username": username,
                "personid": personid,
                "role": role,
            }
            messagebox.showinfo("Welcome", f"Logged in as {role}")

            # route by role
            if role == "admin":
                self.controller.show_frame("DashboardPage")
            elif role == "hourly":
                self.controller.show_frame("ShiftsPage")
            else:
                messagebox.showerror("Error", "Access denied")

        self.controller.run_db_task(
            task, on_success=ok, on_error=lambda e: messagebox.showerror("DB Error", str(e))
        )
