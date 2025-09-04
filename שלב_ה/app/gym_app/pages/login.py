# -*- coding: utf-8 -*-
"""
Login page:
- Debounces multiple submissions (button + Enter)
- Disables the login button while authenticating
- Routes by role (admin -> Dashboard, hourly -> Shifts)
"""

import tkinter as tk
from tkinter import ttk, messagebox

from gym_app import dao


class LoginPage(ttk.Frame):
    """Simple login form that authenticates against DB function `authenticate_user`."""

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self._submitting = False  # prevents double submission

        wrapper = ttk.Frame(self, padding=24, style="Card.TFrame")
        wrapper.place(relx=0.5, rely=0.5, anchor="center")

        title = ttk.Label(wrapper, text="Sign in", font=("Arial", 20, "bold"))
        title.grid(row=0, column=0, columnspan=2, pady=(0, 12))

        ttk.Label(wrapper, text="Username (PID):").grid(row=1, column=0, sticky="e", padx=6, pady=6)
        self.username_var = tk.StringVar()
        self.username_entry = ttk.Entry(wrapper, textvariable=self.username_var, width=28)
        self.username_entry.grid(row=1, column=1, sticky="w", padx=6, pady=6)

        ttk.Label(wrapper, text="Password:").grid(row=2, column=0, sticky="e", padx=6, pady=6)
        self.password_var = tk.StringVar()
        self.password_entry = ttk.Entry(wrapper, textvariable=self.password_var, width=28, show="*")
        self.password_entry.grid(row=2, column=1, sticky="w", padx=6, pady=6)

        self.login_btn = ttk.Button(wrapper, text="Log in", command=self._on_login_click)
        self.login_btn.grid(row=3, column=0, columnspan=2, pady=(14, 0))

        # Bind Enter on both fields
        self.username_entry.bind("<Return>", self._on_enter)
        self.password_entry.bind("<Return>", self._on_enter)

        # Autofocus
        self.username_entry.focus_set()

    # ---------- Events ----------

    def _on_enter(self, event):
        self._on_login_click()

    def _on_login_click(self):
        if self._submitting:
            return
        username = (self.username_var.get() or "").strip()
        password = (self.password_var.get() or "").strip()
        if not username or not password:
            messagebox.showwarning("Login", "Please enter username and password.")
            return

        # lock UI
        self._submitting = True
        try:
            self.login_btn.config(state="disabled")
        except Exception:
            pass

        def on_ok(row):
            # row is either None, or (user_id, personid, role)
            try:
                if not row:
                    messagebox.showerror("Login", "Access denied. Check username or password.")
                    return

                user_id, personid, role = row
                # Persist session
                self.controller.current_user = {
                    "user_id": user_id,
                    "username": username,
                    "personid": personid,
                    "role": role,
                }

                # Route by role
                if role == "admin":
                    messagebox.showinfo("Login", "Access granted: admin")
                    self.controller.show_frame("DashboardPage")
                elif role == "hourly":
                    messagebox.showinfo("Login", "Access granted: hourly worker")
                    self.controller.show_frame("ShiftsPage")
                else:
                    # fallback to dashboard for any other role
                    messagebox.showinfo("Login", f"Access granted: {role}")
                    self.controller.show_frame("DashboardPage")
            finally:
                # unlock UI
                self._submitting = False
                try:
                    self.login_btn.config(state="normal")
                except Exception:
                    pass

        def on_err(exc):
            try:
                messagebox.showerror("Login error", str(exc))
            finally:
                self._submitting = False
                try:
                    self.login_btn.config(state="normal")
                except Exception:
                    pass

        # Background DB call
        self.controller.run_db_task(dao.authenticate_user, username, password, on_success=on_ok, on_error=on_err)

    # API called by App when page is shown
    def on_show(self):
        # clear fields on every show for safety
        self.username_var.set("")
        self.password_var.set("")
        self._submitting = False
        try:
            self.login_btn.config(state="normal")
        except Exception:
            pass
        self.username_entry.focus_set()
