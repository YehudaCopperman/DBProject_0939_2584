# -*- coding: utf-8 -*-
from tkinter import ttk, messagebox
from ..ui.base import BasePage


class DashboardPage(BasePage):
    """
    Admin dashboard (centered, symmetric layout).
    Tiles:
      - Persons
      - Members
      - Shifts
      - Reports
      - Data Manager (admin only, but dashboard is admin-only anyway)
      - Logout
    """

    def __init__(self, parent, controller):
        super().__init__(parent, controller, "Dashboard")

        # Wrapper centered content inside the card
        self.center = ttk.Frame(self.card, padding=16, style="Card.TFrame")
        self.center.pack(expand=True)
        self.center.grid_columnconfigure(0, weight=1)
        self.center.grid_columnconfigure(1, weight=1)

        # Subtitle
        subtitle = ttk.Label(self.center, text="Select an area to manage",
                             style="SubTitle.TLabel")
        subtitle.grid(row=0, column=0, columnspan=2, sticky="n", pady=(0, 12))

        # Build tiles in a symmetric 2-column grid
        # (text, target_frame_name or None for logout)
        tiles = [
            ("Persons", "PersonsPage"),
            ("Members", "MembersPage"),
            ("Shifts", "ShiftsPage"),
            ("Reports", "ReportsPage"),
            ("Data Manager", "DataManagerPage"),
            ("Logout", None),
        ]

        # Keep a reference to buttons if needed later
        self._buttons = []

        r = 1
        c = 0
        for text, target in tiles:
            btn = ttk.Button(
                self.center,
                text=text,
                style="Nav.TButton",
                command=(self._nav_to(target) if target else self._logout)
            )
            # Make the buttons visually consistent and wide
            btn.grid(row=r, column=c, sticky="nsew", padx=12, pady=10, ipadx=30, ipady=10)
            self._buttons.append(btn)

            # two columns
            c = 1 - c
            if c == 0:
                r += 1

        # Ensure rows expand equally for a balanced look
        for i in range(1, r + (1 if c == 1 else 0)):
            self.center.grid_rowconfigure(i, weight=1)

    # ---------- lifecycle ----------
    def on_show(self):
        """Admin-only guard; redirect if non-admin somehow reached here."""
        role = (self.controller.current_user or {}).get("role")
        if role != "admin":
            messagebox.showwarning("Access control", "Dashboard is available for admins only.")
            self.controller.show_frame("ShiftsPage" if role == "hourly" else "LoginPage")

    # ---------- actions ----------
    def _nav_to(self, frame_name: str):
        return lambda: self.controller.show_frame(frame_name)

    def _logout(self):
        self.controller.current_user = {
            "user_id": None,
            "username": None,
            "personid": None,
            "role": None,
        }
        self.controller.show_frame("LoginPage")
