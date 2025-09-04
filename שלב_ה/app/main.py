# -*- coding: utf-8 -*-
"""
Tkinter entry-point and application shell.
- Adds a persistent top toolbar with Back / Dashboard / Logout
- Manages navigation stack for Back
- Runs DB tasks on a background thread with safe error binding
"""

import threading
import tkinter as tk
from tkinter import ttk, messagebox

from gym_app.db import connect   # context manager that yields a psycopg2 connection
from gym_app.config import APP_TITLE
from gym_app.pages.login import LoginPage
from gym_app.pages.dashboard import DashboardPage
from gym_app.pages.persons import PersonsPage
from gym_app.pages.members import MembersPage       # make sure this file exists
from gym_app.pages.data_manager import DataManagerPage
from gym_app.pages.shifts import ShiftsPage
from gym_app.pages.reports import ReportsPage


class App(tk.Tk):
    """Main Tk application: manages navigation, session, and DB background tasks."""

    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1100x800")
        self.minsize(980, 680)

        # Current logged-in user (dict with user_id, username, personid, role)
        self.current_user = {"user_id": None, "username": None, "personid": None, "role": None}

        # Navigation stack (for Back)
        self._nav_stack: list[str] = []
        self._current_frame_name: str | None = None

        # ---------- Top toolbar (visible Back/Dashboard/Logout) ----------
        self.toolbar = ttk.Frame(self, padding=(10, 8))
        self.toolbar.pack(side="top", fill="x")

        # Left side: navigation buttons
        left = ttk.Frame(self.toolbar)
        left.pack(side="left", anchor="w")

        self.btn_back = ttk.Button(left, text="← Back", command=self.go_back)
        self.btn_back.pack(side="left", padx=(0, 8))

        self.btn_home = ttk.Button(left, text="🏠 Dashboard", command=lambda: self.show_frame("DashboardPage"))
        self.btn_home.pack(side="left", padx=(0, 8))

        # Right side: user info + logout
        right = ttk.Frame(self.toolbar)
        right.pack(side="right", anchor="e")

        self.user_label_var = tk.StringVar(value="")
        self.user_label = ttk.Label(right, textvariable=self.user_label_var)
        self.user_label.pack(side="left", padx=(0, 10))

        self.btn_logout = ttk.Button(right, text="Logout", command=self.logout)
        self.btn_logout.pack(side="left")

        # Divider
        sep = ttk.Separator(self, orient="horizontal")
        sep.pack(side="top", fill="x")

        # ---------- Page container ----------
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # Pages registry (include MembersPage!)
        self.frames = {}
        for Page in (
            LoginPage, DashboardPage, PersonsPage, MembersPage,
            DataManagerPage, ShiftsPage, ReportsPage
        ):
            name = Page.__name__
            frame = Page(parent=container, controller=self)
            self.frames[name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        # Go to login on start
        self.show_frame("LoginPage")
        self._init_theme()
        self._update_toolbar_state()

        # Keyboard shortcut for Back
        self.bind_all("<Alt-Left>", lambda e: self.go_back())

    # --------------- UI helpers ---------------

    def _init_theme(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("Card.TFrame", background="#ffffff")
        style.configure("Primary.TButton", padding=6)
        style.configure("Ghost.TButton", padding=6)
        style.configure("Danger.TButton", padding=6, foreground="#b00020")
        style.configure("Nav.TButton", padding=8)

    def _update_toolbar_state(self):
        """Update Back button enabled/disabled and user label."""
        can_go_back = bool(self._nav_stack)
        state = "normal" if can_go_back else "disabled"
        try:
            self.btn_back.config(state=state)
        except Exception:
            pass

        user = self.current_user or {}
        uname = user.get("username")
        role = user.get("role")
        if uname and role:
            self.user_label_var.set(f"Signed in as: {uname} ({role})")
        else:
            self.user_label_var.set("Not signed in")

    def logout(self):
        """Clear session and go to login."""
        self.current_user = {"user_id": None, "username": None, "personid": None, "role": None}
        self._nav_stack.clear()
        self._current_frame_name = None
        self.show_frame("LoginPage")

    def show_frame(self, name: str):
        """Show a frame by its class name, keeping a simple history for 'Back'."""
        if name not in self.frames:
            messagebox.showerror("Navigation", f"Unknown page: {name}")
            return

        # Push current page to stack (if any and not navigating to the same page)
        if self._current_frame_name and self._current_frame_name != name:
            self._nav_stack.append(self._current_frame_name)

        frame = self.frames[name]
        frame.tkraise()
        self._current_frame_name = name

        # If login just occurred, update the toolbar user label
        self._update_toolbar_state()

        if hasattr(frame, "on_show") and callable(frame.on_show):
            frame.on_show()

    def go_back(self):
        """Navigate to the previous frame if available, else go home."""
        while self._nav_stack:
            prev = self._nav_stack.pop()
            if prev != self._current_frame_name:
                self.frames[prev].tkraise()
                self._current_frame_name = prev
                self._update_toolbar_state()
                if hasattr(self.frames[prev], "on_show") and callable(self.frames[prev].on_show):
                    self.frames[prev].on_show()
                return
        # Fallback: Dashboard
        if self._current_frame_name != "DashboardPage":
            self.show_frame("DashboardPage")
        self._update_toolbar_state()

    # --------------- DB background runner ---------------

    def run_db_task(self, task, *args, on_success=None, on_error=None):
        """
        Run a DB task on a background thread.
        task signature: task(conn, *args) or task(conn)
        """

        def runner():
            try:
                with connect() as conn:
                    result = task(conn, *args) if args else task(conn)
                if on_success:
                    self.after(0, lambda res=result: on_success(res))
            except Exception as e:
                if on_error:
                    self.after(0, lambda exc=e: on_error(exc))
                else:
                    self.after(0, lambda exc=e: messagebox.showerror("DB Error", str(exc)))

        threading.Thread(target=runner, daemon=True).start()


if __name__ == "__main__":
    app = App()
    app.mainloop()
