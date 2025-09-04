from tkinter import ttk
from ..ui.base import BasePage


class DashboardPage(BasePage):
    """
    Admin landing page with navigation shortcuts only.
    (Password reset moved to the dedicated Change Password screen.)
    """

    def __init__(self, parent, controller):
        super().__init__(parent, controller, "Dashboard")

        # Top navigation
        nav = ttk.Frame(self.card, padding=12, style="Card.TFrame")
        nav.pack(fill="x", pady=8)

        ttk.Button(
            nav, text="Persons", style="Nav.TButton",
            command=lambda: controller.show_frame("PersonsPage")
        ).pack(anchor="w", pady=4)

        ttk.Button(
            nav, text="Members", style="Nav.TButton",
            command=lambda: controller.show_frame("MembersPage")
        ).pack(anchor="w", pady=4)

        ttk.Button(
            nav, text="Shifts", style="Nav.TButton",
            command=lambda: controller.show_frame("ShiftsPage")
        ).pack(anchor="w", pady=4)

        ttk.Button(
            nav, text="Reports", style="Nav.TButton",
            command=lambda: controller.show_frame("ReportsPage")
        ).pack(anchor="w", pady=4)

        # Data Manager (admin-only page; that screen itself guards role)
        ttk.Button(
            nav, text="Data Manager", style="Nav.TButton",
            command=lambda: controller.show_frame("DataManagerPage")
        ).pack(anchor="w", pady=4)

        # Logout
        ttk.Button(
            nav, text="Logout", style="Ghost.TButton",
            command=self._logout
        ).pack(anchor="w", pady=(12, 0))

    def _logout(self):
        """Clear session and navigate back to Login page."""
        self.controller.current_user = {
            "user_id": None,
            "username": None,
            "personid": None,
            "role": None,
        }
        self.controller.show_frame("LoginPage")
