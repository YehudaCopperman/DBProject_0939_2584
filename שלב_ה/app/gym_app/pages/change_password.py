# -*- coding: utf-8 -*-
"""
ChangePasswordPage:
- All users: change own password (current -> new)
- Admin only: reset hourly worker password to default (PID)
  * Admin section is completely hidden for non-admin users.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from gym_app import dao


class ChangePasswordPage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        root = ttk.Frame(self, padding=16)
        root.pack(fill="both", expand=True)

        title = ttk.Label(root, text="Change Password", font=("Arial", 18, "bold"))
        title.pack(anchor="w", pady=(0, 12))

        # --- Change my own password ---
        my_grp = ttk.LabelFrame(root, text="Change my password", padding=12)
        my_grp.pack(fill="x", pady=6)

        frm = ttk.Frame(my_grp)
        frm.pack(fill="x")

        ttk.Label(frm, text="Current password:").grid(row=0, column=0, sticky="e", padx=6, pady=6)
        self.cur_pw = tk.StringVar()
        ttk.Entry(frm, textvariable=self.cur_pw, show="*").grid(row=0, column=1, sticky="w", padx=6, pady=6)

        ttk.Label(frm, text="New password:").grid(row=1, column=0, sticky="e", padx=6, pady=6)
        self.new_pw = tk.StringVar()
        ttk.Entry(frm, textvariable=self.new_pw, show="*").grid(row=1, column=1, sticky="w", padx=6, pady=6)

        ttk.Label(frm, text="Confirm new password:").grid(row=2, column=0, sticky="e", padx=6, pady=6)
        self.new_pw2 = tk.StringVar()
        ttk.Entry(frm, textvariable=self.new_pw2, show="*").grid(row=2, column=1, sticky="w", padx=6, pady=6)

        ttk.Button(my_grp, text="Update my password", command=self._change_my_password).pack(anchor="e", pady=6)

        # --- Admin-only: reset hourly by PID ---
        self.admin_grp = ttk.LabelFrame(root, text="Admin: reset hourly worker password (PID)", padding=12)
        self.admin_grp.pack(fill="x", pady=12)

        afr = ttk.Frame(self.admin_grp)
        afr.pack(fill="x")

        ttk.Label(afr, text="Target PID:").grid(row=0, column=0, sticky="e", padx=6, pady=6)
        self.target_pid = tk.StringVar()
        ttk.Entry(afr, textvariable=self.target_pid, width=20).grid(row=0, column=1, sticky="w", padx=6, pady=6)

        ttk.Button(self.admin_grp, text="Reset to default (PID)", command=self._reset_hourly_password).pack(anchor="e", pady=6)

    def on_show(self):
        role = (self.controller.current_user or {}).get("role")
        # Show admin tools only for admin; hide entirely for others
        if role == "admin":
            if not self.admin_grp.winfo_ismapped():
                self.admin_grp.pack(fill="x", pady=12)
            # ensure children are enabled
            for child in self.admin_grp.winfo_children():
                try:
                    child.configure(state="normal")
                except Exception:
                    pass
        else:
            if self.admin_grp.winfo_ismapped():
                self.admin_grp.pack_forget()

    # ----- Actions -----

    def _change_my_password(self):
        pid = (self.controller.current_user or {}).get("personid")
        if not pid:
            messagebox.showerror("Error", "Not signed in.")
            return

        cur = self.cur_pw.get() or ""
        npw = self.new_pw.get() or ""
        npw2 = self.new_pw2.get() or ""

        if not cur or not npw or not npw2:
            messagebox.showwarning("Validation", "Please fill all fields.")
            return
        if npw != npw2:
            messagebox.showwarning("Validation", "New passwords do not match.")
            return
        if len(npw) < 4:
            messagebox.showwarning("Validation", "Choose a longer password (≥ 4 chars).")
            return

        def on_ok(ok):
            if ok:
                messagebox.showinfo("Success", "Password updated.")
                self.cur_pw.set("")
                self.new_pw.set("")
                self.new_pw2.set("")
            else:
                messagebox.showerror("Error", "Current password is incorrect.")

        def on_err(exc):
            messagebox.showerror("Error", str(exc))

        self.controller.run_db_task(dao.change_password_by_pid, pid, cur, npw, on_success=on_ok, on_error=on_err)

    def _reset_hourly_password(self):
        role = (self.controller.current_user or {}).get("role")
        if role != "admin":
            messagebox.showerror("Access", "Only admin can perform this action.")
            return

        try:
            tgt = int((self.target_pid.get() or "").strip())
        except Exception:
            messagebox.showwarning("Validation", "Enter a valid numeric PID.")
            return

        # Validate that target is hourly and NOT admin
        def task(conn):
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM worker WHERE pid=%s AND lower(job)='manager'", (tgt,))
                is_admin = cur.fetchone() is not None
                cur.execute("SELECT 1 FROM hourly WHERE pid=%s", (tgt,))
                is_hourly = cur.fetchone() is not None
            return (is_admin, is_hourly)

        def after_check(flags):
            is_admin, is_hourly = flags
            if is_admin:
                messagebox.showerror("Access", "Cannot reset another admin's password.")
                return
            if not is_hourly:
                messagebox.showerror("Validation", "PID is not an hourly worker.")
                return

            def on_ok(_):
                messagebox.showinfo("Success", f"Password of PID {tgt} was reset to default (their PID).")
                self.target_pid.set("")

            def on_err(exc):
                messagebox.showerror("Error", str(exc))

            self.controller.run_db_task(dao.admin_reset_password_by_pid, tgt, on_success=on_ok, on_error=on_err)

        def on_err(exc):
            messagebox.showerror("Error", str(exc))

        self.controller.run_db_task(task, on_success=after_check, on_error=on_err)
