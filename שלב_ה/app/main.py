import sys
import tkinter as tk
from tkinter import ttk, messagebox
import concurrent.futures as futures

from gym_app.config import DBConfig
from gym_app.db import Database
from gym_app.ui.styles import setup_styles

from gym_app.pages.login import LoginPage
from gym_app.pages.dashboard import DashboardPage
from gym_app.pages.persons import PersonsPage
from gym_app.pages.members import MembersPage
from gym_app.pages.shifts import ShiftsPage
from gym_app.pages.reports import ReportsPage
from gym_app.pages.data_manager import DataManagerPage

# Added: ensure-default-admin bootstrap on app start
from gym_app import dao


class GymApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gym Management System")
        self.geometry("1200x800")

        # macOS scaling fix to avoid NSButton min-height warnings
        if sys.platform == "darwin":
            try:
                self.tk.call("tk", "scaling", 1.0)
            except tk.TclError:
                pass

        # Global styles (ttk themes, custom styles, etc.)
        setup_styles(self)

        # In-memory current user session (filled after login)
        self.current_user = {
            "user_id": None,
            "username": None,
            "personid": None,
            "role": None,
        }

        # Database pool + worker thread pool for non-blocking DB work
        self.db = Database(DBConfig())
        self.executor = futures.ThreadPoolExecutor(max_workers=4)

        # Ensure a default admin exists (PID=1, username=1, password=1) IFF no admins exist
        try:
            with self.db.connect() as conn:
                dao.ensure_default_admin(conn)
        except Exception as e:
            # Do not block UI if this fails; log a warning to console
            print("WARN: ensure_default_admin() failed:", e)

        # Busy indicator (appears while DB tasks are running)
        self.busy = ttk.Progressbar(self, mode="indeterminate")
        self._busy = 0

        # Screen container + page registry
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for Page in (
            LoginPage,
            DashboardPage,
            PersonsPage,
            MembersPage,
            ShiftsPage,
            ReportsPage,
            DataManagerPage,
        ):
            name = Page.__name__
            frame = Page(container, self)
            self.frames[name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        # Start at Login
        self.show_frame("LoginPage")

        # Clean shutdown handler
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    # ---------- Navigation ----------
    def show_frame(self, name: str):
        """Raise a page by class name and call its on_show hook if present."""
        frame = self.frames[name]
        frame.tkraise()
        getattr(frame, "on_show", lambda: None)()

    # ---------- Async DB orchestration ----------
    def run_db_task(self, task, *args, on_success=None, on_error=None):
        """
        Run a DB function on a background thread, then post result back to the UI thread.
        - task: callable(conn, *args) → result
        - on_success(result): optional callback on UI thread
        - on_error(exc): optional callback on UI thread
        """
        self._busy_on()

        def call():
            with self.db.connect() as conn:
                return task(conn, *args) if args else task(conn)

        future = self.executor.submit(call)

        def done(f):
            try:
                res = f.result()
                if on_success:
                    self.after(0, lambda: on_success(res))
            except Exception as e:
                if on_error:
                    self.after(0, lambda: on_error(e))
                else:
                    self.after(0, lambda: messagebox.showerror("DB Error", str(e)))
            finally:
                self.after(0, self._busy_off)

        future.add_done_callback(done)

    def _busy_on(self):
        """Show busy indicator when at least one DB task is running."""
        self._busy += 1
        if self._busy == 1:
            self.busy.pack(side="bottom", fill="x")
            self.busy.start(10)
            self.config(cursor="watch")

    def _busy_off(self):
        """Hide busy indicator when all DB tasks are done."""
        self._busy = max(0, self._busy - 1)
        if self._busy == 0:
            self.busy.stop()
            self.busy.pack_forget()
            self.config(cursor="")

    # ---------- App shutdown ----------
    def on_close(self):
        try:
            self.executor.shutdown(wait=False, cancel_futures=True)
        finally:
            try:
                self.db.close_all()
            finally:
                self.destroy()


if __name__ == "__main__":
    app = GymApp()
    app.mainloop()
