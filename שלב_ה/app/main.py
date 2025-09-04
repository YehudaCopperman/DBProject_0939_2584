# -*- coding: utf-8 -*-
"""
Tkinter entry-point and application shell.
- Creates the window and page frames
- Orchestrates background DB tasks with safe error binding
- Adds a global menu bar with Back/Dashboard/Logout
"""

import threading
import tkinter as tk
from tkinter import ttk, messagebox

from gym_app.db import connect   # context manager that yields a psycopg2 connection
from gym_app.config import APP_TITLE
from gym_app.pages.login import LoginPage
from gym_app.pages.dashboard import DashboardPage
from gym_app.pages.persons import PersonsPage
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

        # Root container frame for pages
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # Pages registry
        self.frames = {}
        for Page in (LoginPage, DashboardPage, PersonsPage, DataManagerPage, ShiftsPage, ReportsPage):
            name = Page.__name__
            frame = Page(parent=container, controller=self)
            self.frames[name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        # Build global menu bar
        self._build_menubar()

        # Go to login
        self.show_frame("LoginPage")

        # Basic ttk theme tweaks
        self._init_theme()

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

    def _build_menubar(self):
        menubar = tk.Menu(self)

        # Navigate menu
        nav_menu = tk.Menu(menubar, tearoff=0)
        nav_menu.add_command(label="Back", command=self.go_back, accelerator="Alt+Left")
        nav_menu.add_command(label="Dashboard", command=lambda: self.show_frame("DashboardPage"))
        menubar.add_cascade(label="Navigate", menu=nav_menu)

        # Account menu
        acc_menu = tk.Menu(menubar, tearoff=0)
        acc_menu.add_command(label="Logout", command=self.logout)
        menubar.add_cascade(label="Account", menu=acc_menu)

        self.config(menu=menubar)
        # Keyboard shortcut for Back
        self.bind_all("<Alt-Left>", lambda e: self.go_back())

    def logout(self):
        # Clear session and go to login
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

        if hasattr(frame, "on_show") and callable(frame.on_show):
            frame.on_show()

    def go_back(self):
        """Navigate to the previous frame if available."""
        while self._nav_stack:
            prev = self._nav_stack.pop()
            # Avoid loops if last equals current
            if prev != self._current_frame_name:
                self.show_frame(prev)
                return
        # If no history, go home
        if self._current_frame_name != "DashboardPage":
            self.show_frame("DashboardPage")

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
                    # bind 'result' as default argument to keep its value
                    self.after(0, lambda res=result: on_success(res))
            except Exception as e:
                # bind 'e' so the lambda captures the exception value safely
                if on_error:
                    self.after(0, lambda exc=e: on_error(exc))
                else:
                    self.after(0, lambda exc=e: messagebox.showerror("DB Error", str(exc)))

        threading.Thread(target=runner, daemon=True).start()


if __name__ == "__main__":
    app = App()
    app.mainloop()
