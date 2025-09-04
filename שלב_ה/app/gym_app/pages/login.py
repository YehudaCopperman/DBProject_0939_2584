# -*- coding: utf-8 -*-
"""
Login page:
- Debounces multiple submissions (button + Enter)
- Disables the login button while authenticating
- Routes by role:
    admin  -> Dashboard
    hourly -> Shifts
"""
import tkinter as tk
from tkinter import ttk, messagebox
from gym_app import dao


class LoginPage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self._submitting = False

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

        # Enter bindings
        self.username_entry.bind("<Return>", self._on_enter)
        self.password_entry.bind("<Return>", self._on_enter)

        self.username_entry.focus_set()

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

        self._submitting = True
        try:
            self.login_btn.config(state="disabled")
        except Exception:
            pass

        def on_ok(row):
            try:
                if not row:
                    messagebox.showerror("Login", "Access denied. Check username or password.")
                    return

                user_id, personid, role = row
                # Only admin/hourly allowed (DB already ensures this)
                self.controller.current_user = {
                    "user_id": user_id,
                    "username": username,
                    "personid": personid,
                    "role": role,
                }

                if role == "admin":
                    self.controller.show_frame("DashboardPage")
                elif role == "hourly":
                    self.controller.show_frame("ShiftsPage")
                else:
                    messagebox.showerror("Login", "Role not permitted.")
            finally:
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

        self.controller.run_db_task(dao.authenticate_user, username, password, on_success=on_ok, on_error=on_err)

    def on_show(self):
        self.username_var.set("")
        self.password_var.set("")
        self._submitting = False
        try:
            self.login_btn.config(state="normal")
        except Exception:
            pass
        self.username_entry.focus_set()
