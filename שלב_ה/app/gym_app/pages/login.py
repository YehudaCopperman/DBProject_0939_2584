# -*- coding: utf-8 -*-
"""
Login page (English, centered, symmetric):
- Debounced submit (button & Enter)
- Disable button while authenticating
- Show/Hide password toggle
- Routes by role: admin -> Dashboard, hourly -> Shifts
"""

import tkinter as tk
from tkinter import ttk, messagebox
from gym_app import dao


class LoginPage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self._submitting = False

        # Centered card
        wrapper = ttk.Frame(self, padding=24, style="Card.TFrame")
        wrapper.place(relx=0.5, rely=0.5, anchor="center")

        title = ttk.Label(wrapper, text="Sign in", style="Title.TLabel")
        subtitle = ttk.Label(wrapper, text="Enter your credentials to continue", style="SubTitle.TLabel")
        title.grid(row=0, column=0, columnspan=3, pady=(0, 4))
        subtitle.grid(row=1, column=0, columnspan=3, pady=(0, 16))

        # Username
        ttk.Label(wrapper, text="Username (PID):").grid(row=2, column=0, sticky="e", padx=6, pady=6)
        self.username_var = tk.StringVar()
        self.username_entry = ttk.Entry(wrapper, textvariable=self.username_var, width=28)
        self.username_entry.grid(row=2, column=1, columnspan=2, sticky="w", padx=6, pady=6)

        # Password + show/hide
        ttk.Label(wrapper, text="Password:").grid(row=3, column=0, sticky="e", padx=6, pady=6)
        self.password_var = tk.StringVar()
        self.password_entry = ttk.Entry(wrapper, textvariable=self.password_var, width=28, show="*")
        self.password_entry.grid(row=3, column=1, sticky="w", padx=6, pady=6)

        self._pw_visible = tk.BooleanVar(value=False)
        toggle = ttk.Checkbutton(
            wrapper, text="Show", variable=self._pw_visible,
            command=self._toggle_password
        )
        toggle.grid(row=3, column=2, sticky="w", padx=(6, 0))

        # Submit
        self.login_btn = ttk.Button(wrapper, text="Log in", style="Primary.TButton", command=self._on_login_click)
        self.login_btn.grid(row=4, column=0, columnspan=3, pady=(14, 0), ipadx=16, ipady=2)

        # Enter bindings
        self.username_entry.bind("<Return>", self._on_enter)
        self.password_entry.bind("<Return>", self._on_enter)

        # Focus flow
        self.username_entry.focus_set()

        # Grid breathing space
        for c in range(3):
            wrapper.grid_columnconfigure(c, weight=1)

    # --- UI helpers ---
    def _toggle_password(self):
        self.password_entry.configure(show="" if self._pw_visible.get() else "*")

    def _on_enter(self, _event):
        self._on_login_click()

    # --- Auth flow ---
    def _on_login_click(self):
        if self._submitting:
            return

        username = (self.username_var.get() or "").strip()
        password = (self.password_var.get() or "").strip()
        if not username or not password:
            messagebox.showwarning("Login", "Please enter both username and password.")
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
                # Allow only admin / hourly
                if role not in ("admin", "hourly"):
                    messagebox.showerror("Login", "Your role is not permitted to access the system.")
                    return

                self.controller.current_user = {
                    "user_id": user_id,
                    "username": username,
                    "personid": personid,
                    "role": role,
                }

                self.controller.show_frame("DashboardPage" if role == "admin" else "ShiftsPage")
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
        # Reset fields each time login page is shown
        self.username_var.set("")
        self.password_var.set("")
        self._pw_visible.set(False)
        self.password_entry.configure(show="*")
        self._submitting = False
        try:
            self.login_btn.config(state="normal")
        except Exception:
            pass
        self.username_entry.focus_set()
