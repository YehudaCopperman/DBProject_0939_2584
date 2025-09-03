
# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk
from ..ui.base import BasePage

class DashboardPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, "מסך ראשי")
        nav = ttk.Frame(self.card, padding=(12,12), style="Card.TFrame")
        nav.pack(side="left", fill="y")
        main = ttk.Frame(self.card, padding=(12,12), style="Card.TFrame")
        main.pack(side="right", fill="both", expand=True)

        def nav_btn(text, page):
            return ttk.Button(nav, text=text, style="Nav.TButton",
                              command=lambda: controller.show_frame(page))

        nav_btn("ניהול אנשים", "PersonsPage").pack(fill="x", pady=4)
        nav_btn("ניהול חברים", "MembersPage").pack(fill="x", pady=4)
        nav_btn("משמרות", "ShiftsPage").pack(fill="x", pady=4)
        nav_btn("דוחות ושגרות", "ReportsPage").pack(fill="x", pady=4)
        ttk.Separator(nav).pack(fill="x", pady=8)
        nav_btn("יציאה", "LoginPage").pack(fill="x", pady=4)

        ttk.Label(main, text="ברוך הבא למערכת ניהול חדר כושר", style="Title.TLabel").pack(anchor="w")
        ttk.Label(main, text="בחר פעולה מתפריט הניווט.", style="SubTitle.TLabel").pack(anchor="w", pady=(6,0))
