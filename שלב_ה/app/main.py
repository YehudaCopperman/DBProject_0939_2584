# -*- coding: utf-8 -*-
"""
App shell:
- Top toolbar: Back / Dashboard / Change Password / Logout
- Role guard:
    admin  -> full app
    hourly -> ShiftsPage + ChangePasswordPage only (read-only)
    others -> Login only
"""

import threading
import tkinter as tk
from tkinter import ttk, messagebox

from gym_app.db import connect
from gym_app.config import APP_TITLE
from gym_app.pages.login import LoginPage
from gym_app.pages.dashboard import DashboardPage
from gym_app.pages.persons import PersonsPage
from gym_app.pages.members import MembersPage
from gym_app.pages.data_manager import DataManagerPage
from gym_app.pages.shifts import ShiftsPage
from gym_app.pages.reports import ReportsPage
from gym_app.pages.change_password import ChangePasswordPage


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1100x800")
        self.minsize(980, 680)

        self.current_user = {"user_id": None, "username": None, "personid": None, "role": None}
        self._nav_stack = []
        self._current_frame_name = None

        # Toolbar
        self.toolbar = ttk.Frame(self, padding=(10, 8))
        self.toolbar.pack(side="top", fill="x")

        left = ttk.Frame(self.toolbar); left.pack(side="left", anchor="w")
        self.btn_back = ttk.Button(left, text="← Back", command=self.go_back); self.btn_back.pack(side="left", padx=(0, 8))
        self.btn_home = ttk.Button(left, text="🏠 Dashboard", command=lambda: self.show_frame("DashboardPage")); self.btn_home.pack(side="left", padx=(0, 8))

        right = ttk.Frame(self.toolbar); right.pack(side="right", anchor="e")
        self.user_label_var = tk.StringVar(value=""); ttk.Label(right, textvariable=self.user_label_var).pack(side="left", padx=(0, 10))
        self.btn_change_pw = ttk.Button(right, text="Change Password", command=lambda: self.show_frame("ChangePasswordPage")); self.btn_change_pw.pack(side="left", padx=(0, 8))
        ttk.Button(right, text="Logout", command=self.logout).pack(side="left")

        ttk.Separator(self, orient="horizontal").pack(side="top", fill="x")

        # Container + pages
        container = ttk.Frame(self); container.pack(fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1); container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for Page in (LoginPage, DashboardPage, PersonsPage, MembersPage, DataManagerPage, ShiftsPage, ReportsPage, ChangePasswordPage):
            name = Page.__name__
            frame = Page(parent=container, controller=self)
            self.frames[name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self._init_theme()
        self.show_frame("LoginPage")
        self._update_toolbar_state()
        self.bind_all("<Alt-Left>", lambda e: self.go_back())

    def _init_theme(self):
        st = ttk.Style(self)
        try: st.theme_use("clam")
        except Exception: pass
        st.configure("Card.TFrame", background="#ffffff")

    # -------- Role guard --------
    def _is_allowed_for_role(self, name: str) -> bool:
        role = (self.current_user or {}).get("role")
        if role == "admin":
            return True
        if role == "hourly":
            return name in ("ShiftsPage", "ChangePasswordPage", "LoginPage")
        return name == "LoginPage"

    def _update_toolbar_state(self):
        self.btn_back.config(state=("normal" if self._nav_stack else "disabled"))
        role = (self.current_user or {}).get("role")
        uname = (self.current_user or {}).get("username")
        self.user_label_var.set(f"Signed in as: {uname} ({role})" if uname and role else "Not signed in")
        self.btn_home.config(state=("disabled" if role == "hourly" else "normal"))
        self.btn_change_pw.config(state=("normal" if role in ("admin", "hourly") else "disabled"))

    def logout(self):
        self.current_user = {"user_id": None, "username": None, "personid": None, "role": None}
        self._nav_stack.clear(); self._current_frame_name = None
        self.show_frame("LoginPage")

    def show_frame(self, name: str):
        if name not in self.frames:
            messagebox.showerror("Navigation", f"Unknown page: {name}"); return
        if not self._is_allowed_for_role(name):
            messagebox.showwarning("Access control", "You don't have permission to open this screen.")
            self._nav_stack.clear()
            role = (self.current_user or {}).get("role")
            name = "ShiftsPage" if role == "hourly" else ("DashboardPage" if role == "admin" else "LoginPage")

        if self._current_frame_name and self._current_frame_name != name:
            self._nav_stack.append(self._current_frame_name)

        frame = self.frames[name]; frame.tkraise(); self._current_frame_name = name
        self._update_toolbar_state()
        if hasattr(frame, "on_show") and callable(frame.on_show): frame.on_show()

    def go_back(self):
        while self._nav_stack:
            prev = self._nav_stack.pop()
            if prev != self._current_frame_name and self._is_allowed_for_role(prev):
                self.frames[prev].tkraise(); self._current_frame_name = prev; self._update_toolbar_state()
                if hasattr(self.frames[prev], "on_show") and callable(self.frames[prev].on_show): self.frames[prev].on_show()
                return
        role = (self.current_user or {}).get("role")
        target = "DashboardPage" if role == "admin" else ("ShiftsPage" if role == "hourly" else "LoginPage")
        if self._current_frame_name != target: self.show_frame(target)
        self._update_toolbar_state()

    # -------- DB runner --------
    def run_db_task(self, task, *args, on_success=None, on_error=None):
        def runner():
            try:
                with connect() as conn:
                    result = task(conn, *args) if args else task(conn)
                if on_success: self.after(0, lambda res=result: on_success(res))
            except Exception as e:
                if on_error: self.after(0, lambda exc=e: on_error(exc))
                else: self.after(0, lambda exc=e: messagebox.showerror("DB Error", str(exc)))
        threading.Thread(target=runner, daemon=True).start()


if __name__ == "__main__":
    App().mainloop()


