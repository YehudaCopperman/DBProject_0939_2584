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


class GymApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("מערכת ניהול חדר כושר")
        self.geometry("1200x800")

        # התאמת סקיילינג ל-macOS כדי להימנע מ-Warning של NSButton
        if sys.platform == 'darwin':
            try:
                self.tk.call('tk', 'scaling', 1.0)
            except tk.TclError:
                pass

        setup_styles(self)

        # שמירת משתמש נוכחי בסשן
        self.current_user = {"user_id": None, "username": None, "personid": None, "role": None}

        # DB + ThreadPool לריצות לא חוסמות UI
        self.db = Database(DBConfig())
        self.executor = futures.ThreadPoolExecutor(max_workers=4)

        # אינדיקציית Busy
        self.busy = ttk.Progressbar(self, mode="indeterminate")
        self._busy = 0

        # ניווט מסכים
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for Page in (LoginPage, DashboardPage, PersonsPage, MembersPage, ShiftsPage, ReportsPage):
            name = Page.__name__
            frame = Page(container, self)
            self.frames[name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("LoginPage")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def show_frame(self, name: str):
        f = self.frames[name]
        f.tkraise()
        getattr(f, 'on_show', lambda: None)()

    def run_db_task(self, task, *args, on_success=None, on_error=None):
        """מריץ פעולה על ה-DB ב-Thread נפרד ומשיב לתוצאה חזרה ל-UI."""
        self._busy_on()

        def call():
            with self.db.connect() as conn:
                return task(conn, *args) if args else task(conn)

        fut = self.executor.submit(call)

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

        fut.add_done_callback(done)

    def _busy_on(self):
        self._busy += 1
        if self._busy == 1:
            self.busy.pack(side="bottom", fill="x")
            self.busy.start(10)
            self.config(cursor="watch")

    def _busy_off(self):
        self._busy = max(0, self._busy - 1)
        if self._busy == 0:
            self.busy.stop()
            self.busy.pack_forget()
            self.config(cursor="")

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
