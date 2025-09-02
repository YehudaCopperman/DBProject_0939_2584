# -*- coding: utf-8 -*-
"""
Gym DB UI – Tkinter + psycopg2 connection pool + async workers
שיפורים עיקריים:
- שימוש ב-Connection Pool (לא משתפים חיבור יחיד בין threads)
- worker threads כ-daemon + תור תוצאות מסודר
- אינדיקציית Busy אמיתית (cursor+תווית) לאורך המשימה
- טעינה מוגבלת של רשומות (LIMIT) במקום למשוך את כל הטבלה
- שאילתות מהירות יותר (טווח תאריכים במקום EXTRACT)
"""
import tkinter as tk
from tkinter import messagebox, ttk
from datetime import date
import threading
import queue
from contextlib import contextmanager

import psycopg2
from psycopg2 import Error
from psycopg2 import pool


# --- הגדרות חיבור למסד (עדכנו לפי הצורך) ---
DB_USER = "yehuda"
DB_PASSWORD = "ninga"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "gym_db"


# --- אתחול Connection Pool + קונטקסט מנג'ר לחיבור ---
def init_pool():
    return pool.SimpleConnectionPool(
        minconn=1,
        maxconn=6,  # אפשר להתאים לפי העומס
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME
    )

@contextmanager
def get_conn(db_pool):
    conn = db_pool.getconn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        db_pool.putconn(conn)


# --- מחלקת ניהול האפליקציה (החלק המרכזי שמנהל את המסכים) ---
class GymApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("מערכת ניהול חדר כושר")
        self.geometry("1000x800")
        self.current_user = None

        # אתחול pool
        try:
            self.db_pool = init_pool()
        except (Exception, Error) as e:
            messagebox.showerror("Database Error", f"Failed to open connection pool: {e}")
            self.destroy()
            return

        # תור להעברת תוצאות מה-thread-ים הרצים ברקע
        self.db_queue = queue.Queue()
        self.pending_tasks = 0  # כמה משימות פעילות כרגע

        # תווית "טוען..."
        self.loading_label = tk.Label(self, text="טוען...", font=("Arial", 14), fg="blue")
        self.loading_label.pack_forget()

        # מיכל למסכים
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # יצירת המסכים
        self.frames = {}
        for F in (LoginPage, DashboardPage, MemberManagementPage, QueriesAndProceduresPage):
            page_name = F.__name__
            frame = F(parent=container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("LoginPage")
        self.after(100, self.process_db_queue)

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()
        if hasattr(frame, 'on_show'):
            frame.on_show()

    def show_busy(self, on: bool):
        """הצגה/הסתרה של אינדיקציית Busy."""
        if on:
            if not self.loading_label.winfo_ismapped():
                self.loading_label.pack(side="bottom", pady=10)
            self.config(cursor="watch")
        else:
            if self.loading_label.winfo_ismapped():
                self.loading_label.pack_forget()
            self.config(cursor="")

    def run_db_task(self, task, *args, on_success=None, on_error=None):
        """
        מפעיל משימת DB בת’רד רקע.
        task אמורה לקבל פרמטר ראשון conn (חיבור מה-pool), ואח"כ את *args.
        """
        self.pending_tasks += 1
        self.show_busy(True)

        def run_task():
            try:
                with get_conn(self.db_pool) as conn:
                    result = task(conn, *args)
                self.db_queue.put(('success', on_success, result))
            except Exception as e:
                self.db_queue.put(('error', on_error, e))

        threading.Thread(target=run_task, daemon=True).start()

    def process_db_queue(self):
        """מעבד תוצאות ממשימות בסיס הנתונים."""
        try:
            while True:
                status, callback, data = self.db_queue.get_nowait()
                try:
                    if status == 'success' and callback:
                        callback(data)
                    elif status == 'error':
                        if callback:
                            callback(data)
                        else:
                            messagebox.showerror("Database Error", f"An error occurred: {data}")
                finally:
                    self.db_queue.task_done()
                    self.pending_tasks = max(0, self.pending_tasks - 1)
        except queue.Empty:
            pass
        finally:
            if self.pending_tasks == 0:
                self.show_busy(False)
            self.after(100, self.process_db_queue)

    def on_closing(self):
        """סוגר את pool באופן נקי כאשר האפליקציה נסגרת."""
        try:
            if getattr(self, "db_pool", None):
                self.db_pool.closeall()
                messagebox.showinfo("התנתקות", "התנתקת משרת מסד הנתונים בהצלחה.")
        finally:
            self.destroy()


# --- מסך כניסה ---
class LoginPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        frame = tk.Frame(self, padx=20, pady=20)
        frame.place(relx=0.5, rely=0.5, anchor='center')

        tk.Label(frame, text="כניסה למערכת", font=("Arial", 24)).pack(pady=10)
        tk.Label(frame, text="שם משתמש:").pack(pady=5)
        self.username_entry = tk.Entry(frame)
        self.username_entry.pack()
        tk.Label(frame, text="סיסמה:").pack(pady=5)
        self.password_entry = tk.Entry(frame, show="*")
        self.password_entry.pack()
        
        self.login_button = tk.Button(frame, text="התחבר", command=self.check_login)
        self.login_button.pack(pady=10)
        
        # קשירת כפתור Enter ללחיצה
        self.password_entry.bind('<Return>', self.check_login)
        self.username_entry.bind('<Return>', self.check_login)

    def check_login(self, event=None):
        username = self.username_entry.get()
        password = self.password_entry.get()

        if username == "admin" and password == "password":
            messagebox.showinfo("Success", "התחברת בהצלחה!")
            self.controller.show_frame("DashboardPage")
            # ביטול הקישורים כדי למנוע חלונות כפולים
            self.password_entry.unbind('<Return>')
            self.username_entry.unbind('<Return>')
        else:
            messagebox.showerror("Error", "שם משתמש או סיסמה שגויים")


# --- מסך ראשי ---
class DashboardPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        label = tk.Label(self, text="מסך ראשי (Dashboard)", font=("Arial", 24))
        label.pack(pady=100, padx=10)
        
        self.member_btn = tk.Button(self, text="ניהול חברים", command=lambda: self.controller.show_frame("MemberManagementPage"))
        self.member_btn.pack(pady=10)
        
        self.queries_btn = tk.Button(self, text="דוחות ושאילתות", command=lambda: self.controller.show_frame("QueriesAndProceduresPage"))
        self.queries_btn.pack(pady=10)
        
        self.logout_btn = tk.Button(self, text="התנתק", command=lambda: self.controller.show_frame("LoginPage"))
        self.logout_btn.pack(pady=20)
        
        self.bind_keyboard_navigation()

    def bind_keyboard_navigation(self):
        """קשר כפתורי ניווט במקלדת."""
        buttons = [self.member_btn, self.queries_btn, self.logout_btn]
        for i, btn in enumerate(buttons):
            btn.bind('<Up>', lambda event, index=i: self.focus_on_button(buttons, index - 1))
            btn.bind('<Down>', lambda event, index=i: self.focus_on_button(buttons, index + 1))
            btn.bind('<Return>', lambda event: event.widget.invoke())
        self.member_btn.focus_set()

    def focus_on_button(self, buttons, index):
        """מעביר את הפוקוס לכפתור אחר."""
        next_index = index % len(buttons)
        buttons[next_index].focus_set()


# --- מסך ניהול חברים (CRUD) ---
class MemberManagementPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        tk.Label(self, text="ניהול חברים", font=("Arial", 20)).pack(pady=10)

        self.form_frame = tk.LabelFrame(self, text="פרטי חבר", padx=10, pady=10)
        self.form_frame.pack(pady=10)
        
        self.create_form_fields()
        
        button_frame = tk.Frame(self)
        button_frame.pack(pady=10)
        
        self.add_btn = tk.Button(button_frame, text="הוסף חבר", command=self.add_member)
        self.add_btn.pack(side=tk.LEFT, padx=5)
        self.clear_btn = tk.Button(button_frame, text="נקה טופס", command=self.clear_form)
        self.clear_btn.pack(side=tk.LEFT, padx=5)
        self.update_btn = tk.Button(button_frame, text="עדכן", command=self.update_member)
        self.update_btn.pack(side=tk.LEFT, padx=5)
        self.delete_btn = tk.Button(button_frame, text="מחק", command=self.delete_member)
        self.delete_btn.pack(side=tk.LEFT, padx=5)
        
        self.tree_frame = tk.Frame(self)
        self.tree_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        self.tree_scroll = ttk.Scrollbar(self.tree_frame)
        self.tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.member_tree = ttk.Treeview(self.tree_frame, yscrollcommand=self.tree_scroll.set)
        self.member_tree.pack(fill=tk.BOTH, expand=True)
        self.tree_scroll.config(command=self.member_tree.yview)

        self.setup_treeview()
        self.member_tree.bind("<<TreeviewSelect>>", self.select_record)
        
        self.back_btn = tk.Button(self, text="חזרה למסך הראשי", command=lambda: self.controller.show_frame("DashboardPage"))
        self.back_btn.pack(pady=10)
        
        self.bind_keyboard_navigation()

    def bind_keyboard_navigation(self):
        """קשר כפתורי ניווט במקלדת."""
        buttons = [self.add_btn, self.clear_btn, self.update_btn, self.delete_btn]
        for i, btn in enumerate(buttons):
            btn.bind('<Right>', lambda event, index=i: self.focus_on_button(buttons, index + 1))
            btn.bind('<Left>', lambda event, index=i: self.focus_on_button(buttons, index - 1))
            btn.bind('<Return>', lambda event: event.widget.invoke())
        self.back_btn.bind('<Return>', lambda event: event.widget.invoke())
        self.add_btn.focus_set()

    def focus_on_button(self, buttons, index):
        """מעביר את הפוקוס לכפתור אחר."""
        next_index = index % len(buttons)
        buttons[next_index].focus_set()

    def on_show(self):
        """נקרא כאשר המסך הזה מוצג."""
        self.controller.run_db_task(self.load_members_from_db, on_success=self.update_members_tree)

    def create_form_fields(self):
        self.entries = {}
        fields = [
            'PID', 'First Name', 'Last Name', 'Date of Birth (YYYY-MM-DD)',
            'Email', 'Address', 'Phone', 'Membership Type', 'Is Active (True/False)'
        ]
        for i, field in enumerate(fields):
            label = tk.Label(self.form_frame, text=f"{field}:", anchor='w')
            label.grid(row=i, column=0, sticky='w', padx=5, pady=2)
            entry = tk.Entry(self.form_frame)
            entry.grid(row=i, column=1, sticky='ew', padx=5, pady=2)
            self.entries[field] = entry
            entry.bind('<Return>', self.focus_next_entry)
        # מתיחת עמודה 1
        self.form_frame.grid_columnconfigure(1, weight=1)

    def focus_next_entry(self, event):
        """מעביר את הפוקוס לשדה הבא."""
        entries_list = list(self.entries.values())
        current_index = entries_list.index(event.widget)
        if current_index < len(entries_list) - 1:
            entries_list[current_index + 1].focus_set()
        else:
            self.add_btn.focus_set()

    def get_form_data(self):
        data = {key: entry.get() for key, entry in self.entries.items()}
        try:
            data['PID'] = int(data['PID'])
            data['Date of Birth (YYYY-MM-DD)'] = date.fromisoformat(data['Date of Birth (YYYY-MM-DD)'])
            data['Phone'] = int(data['Phone'])
            is_active_str = data['Is Active (True/False)'].strip().lower()
            if is_active_str not in ('true', 'false'):
                raise ValueError("Is Active must be 'True' or 'False'")
            data['Is Active (True/False)'] = (is_active_str == 'true')
        except (ValueError, IndexError) as e:
            messagebox.showerror("שגיאה", f"שגיאת קלט: {e}. ודא שהנתונים בפורמט הנכון.")
            return None
        return data

    def setup_treeview(self):
        cols = (
            'PID', 'First Name', 'Last Name', 'Date of Birth', 'Email',
            'Address', 'Phone', 'Member Type', 'Start Date', 'Is Active'
        )
        self.member_tree['columns'] = cols
        self.member_tree['show'] = 'headings'
        for col in cols:
            self.member_tree.heading(col, text=col)
            self.member_tree.column(col, width=120, anchor='center')

    def load_members_from_db(self, conn):
        """טעינת נתונים מבסיס הנתונים (מוגבל ל-500 רשומות)."""
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT p.pid, p.firstname, p.lastname, p.dateofb, p.email, p.address, p.phone,
                       m.membershiptype, m.memberstartdate, m.isactive
                FROM person p
                JOIN member m ON p.pid = m.personid
                ORDER BY p.pid
                LIMIT 500
            """)
            return cursor.fetchall()

    def update_members_tree(self, rows):
        """מעדכן את הממשק עם התוצאות שהתקבלו."""
        for item in self.member_tree.get_children():
            self.member_tree.delete(item)
        for row in rows:
            # הפיכה למחרוזות כדי למנוע בעיות תצוגה עם טיפוסי תאריך/בוליאני
            safe = list(row)
            safe[3] = safe[3].isoformat() if safe[3] else ""
            safe[8] = safe[8].isoformat() if safe[8] else ""
            safe[9] = "True" if safe[9] else "False"
            self.member_tree.insert('', tk.END, values=tuple(safe))

    def select_record(self, event):
        selected_item = self.member_tree.focus()
        if not selected_item:
            return
        values = self.member_tree.item(selected_item, 'values')
        if not values:
            return
        self.clear_form()
        fields = [
            'PID', 'First Name', 'Last Name', 'Date of Birth (YYYY-MM-DD)',
            'Email', 'Address', 'Phone', 'Membership Type', 'Is Active (True/False)'
        ]
        # כאן הערכים כבר מחרוזות – לא קוראים strftime
        for i, field in enumerate(fields):
            self.entries[field].insert(0, values[i])

    def add_member(self):
        data = self.get_form_data()
        if not data:
            return
        self.controller.run_db_task(
            self._add_member_to_db, data,
            on_success=self.on_success_action,
            on_error=self.on_error_action
        )

    def _add_member_to_db(self, conn, data):
        with conn.cursor() as cursor:
            cursor.execute(
                "CALL register_new_member(%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (data['PID'], data['First Name'], data['Last Name'], data['Date of Birth (YYYY-MM-DD)'],
                 data['Email'], data['Address'], data['Phone'], data['Membership Type'], data['Is Active (True/False)'])
            )
        return "חבר חדש נרשם בהצלחה!"

    def update_member(self):
        data = self.get_form_data()
        if not data:
            return
        self.controller.run_db_task(
            self._update_member_in_db, data,
            on_success=self.on_success_action,
            on_error=self.on_error_action
        )

    def _update_member_in_db(self, conn, data):
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE person
                SET firstname=%s, lastname=%s, dateofb=%s, email=%s, address=%s, phone=%s
                WHERE pid=%s
            """, (data['First Name'], data['Last Name'], data['Date of Birth (YYYY-MM-DD)'],
                  data['Email'], data['Address'], data['Phone'], data['PID']))
            cursor.execute("""
                UPDATE member SET membershiptype=%s, isactive=%s WHERE personid=%s
            """, (data['Membership Type'], data['Is Active (True/False)'], data['PID']))
        return "פרטי החבר עודכנו בהצלחה!"

    def delete_member(self):
        pid = self.entries['PID'].get().strip()
        if not pid:
            messagebox.showerror("שגיאה", "אנא בחר חבר למחיקה.")
            return

        if not messagebox.askyesno("אזהרה", f"האם אתה בטוח שברצונך למחוק את חבר מספר {pid}?"):
            return
        
        self.controller.run_db_task(
            self._delete_member_from_db, pid,
            on_success=self.on_success_action,
            on_error=self.on_error_action
        )

    def _delete_member_from_db(self, conn, pid):
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM member WHERE personid = %s", (pid,))
            cursor.execute("DELETE FROM person WHERE pid = %s", (pid,))
        return "החבר נמחק בהצלחה!"

    def on_success_action(self, message):
        """פעולה שתתבצע לאחר הצלחה בממשק המשתמש."""
        messagebox.showinfo("הצלחה", message)
        self.controller.run_db_task(self.load_members_from_db, on_success=self.update_members_tree)
        self.clear_form()

    def on_error_action(self, error):
        """פעולה שתתבצע לאחר שגיאה בממשק המשתמש."""
        messagebox.showerror("שגיאה", f"שגיאה: {error}")

    def clear_form(self):
        for entry in self.entries.values():
            entry.delete(0, tk.END)


# --- מסך שאילתות ופרוצדורות ---
class QueriesAndProceduresPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        tk.Label(self, text="דוחות, שאילתות ופרוצדורות", font=("Arial", 20)).pack(pady=10)
        
        button_frame = tk.Frame(self)
        button_frame.pack(pady=10)
        
        self.query1_btn = tk.Button(button_frame, text="שעות עבודה לפי חודש", command=self.run_query_1)
        self.query1_btn.pack(side=tk.LEFT, padx=5)
        self.query2_btn = tk.Button(button_frame, text="השירות היקר ביותר", command=self.run_query_2)
        self.query2_btn.pack(side=tk.LEFT, padx=5)
        self.proc_btn = tk.Button(button_frame, text="עדכן חברות שפג תוקפן", command=self.run_procedure_update_memberships)
        self.proc_btn.pack(side=tk.LEFT, padx=5)
        
        self.tree_frame = tk.Frame(self)
        self.tree_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        self.tree_scroll = ttk.Scrollbar(self.tree_frame)
        self.tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.results_tree = ttk.Treeview(self.tree_frame, yscrollcommand=self.tree_scroll.set)
        self.results_tree.pack(fill=tk.BOTH, expand=True)
        self.tree_scroll.config(command=self.results_tree.yview)

        self.back_btn = tk.Button(self, text="חזרה למסך הראשי", command=lambda: self.controller.show_frame("DashboardPage"))
        self.back_btn.pack(pady=10)

        self.bind_keyboard_navigation()

    def bind_keyboard_navigation(self):
        """קשר כפתורי ניווט במקלדת."""
        buttons = [self.query1_btn, self.query2_btn, self.proc_btn, self.back_btn]
        for i, btn in enumerate(buttons):
            btn.bind('<Right>', lambda event, index=i: self.focus_on_button(buttons, index + 1))
            btn.bind('<Left>', lambda event, index=i: self.focus_on_button(buttons, index - 1))
            btn.bind('<Return>', lambda event: event.widget.invoke())
        self.query1_btn.focus_set()

    def focus_on_button(self, buttons, index):
        """מעביר את הפוקוס לכפתור אחר."""
        next_index = index % len(buttons)
        buttons[next_index].focus_set()

    def on_show(self):
        """נקרא כאשר המסך הזה מוצג."""
        self.clear_treeview()

    def clear_treeview(self):
        self.results_tree.delete(*self.results_tree.get_children())
        self.results_tree.config(columns=(), show='headings')

    def run_query_1(self):
        input_window = tk.Toplevel(self)
        input_window.title("הזן חודש ושנה")
        input_window.geometry("300x170")
        
        tk.Label(input_window, text="חודש (1-12):").pack(pady=5)
        month_entry = tk.Entry(input_window)
        month_entry.pack()
        
        tk.Label(input_window, text="שנה (YYYY):").pack(pady=5)
        year_entry = tk.Entry(input_window)
        year_entry.pack()
        
        def execute_query():
            try:
                month = int(month_entry.get())
                year = int(year_entry.get())
                if not (1 <= month <= 12):
                    raise ValueError("חודש חייב להיות בין 1 ל-12")
                self.controller.run_db_task(
                    self._execute_query_1_from_db, month, year,
                    on_success=self.update_query_1_results,
                    on_error=self.on_error_action
                )
                input_window.destroy()
            except ValueError as ex:
                messagebox.showerror("שגיאת קלט", f"אנא הזן מספרים חוקיים. {ex}")

        tk.Button(input_window, text="הרץ", command=execute_query).pack(pady=10)

    def _execute_query_1_from_db(self, conn, month, year):
        # שימוש בטווח תאריכים (מהיר יותר מאשר EXTRACT במקטע WHERE)
        start = date(year, month, 1)
        if month == 12:
            end = date(year + 1, 1, 1)
        else:
            end = date(year, month + 1, 1)
        sql_query = """
        SELECT p.firstname, p.lastname,
               SUM(EXTRACT(EPOCH FROM (s.clock_out - s.clock_in))) / 3600 AS total_hours
        FROM person p
        JOIN shift s ON p.pid = s.pid
        WHERE s.date >= %s AND s.date < %s
        GROUP BY p.pid, p.firstname, p.lastname
        ORDER BY total_hours DESC;
        """
        with conn.cursor() as cursor:
            cursor.execute(sql_query, (start, end))
            return cursor.fetchall()
            
    def update_query_1_results(self, rows):
        self.clear_treeview()
        cols = ("First Name", "Last Name", "Total Hours")
        self.results_tree.config(columns=cols)
        for col in cols:
            self.results_tree.heading(col, text=col)
            self.results_tree.column(col, width=150, anchor='center')
        
        if not rows:
            self.results_tree.insert('', tk.END, values=("לא נמצאו נתונים עבור חודש זה.", "", ""))
        else:
            for row in rows:
                self.results_tree.insert('', tk.END, values=(row[0], row[1], f"{row[2]:.2f}"))

    def run_query_2(self):
        self.controller.run_db_task(
            self._execute_query_2_from_db,
            on_success=self.update_query_2_results,
            on_error=self.on_error_action
        )

    def _execute_query_2_from_db(self, conn):
        # קל ומהיר יותר מ-CTE + MAX
        sql_query = """
        SELECT servicename, SUM(price) AS total
        FROM serves
        GROUP BY servicename
        ORDER BY total DESC
        LIMIT 1;
        """
        with conn.cursor() as cursor:
            cursor.execute(sql_query)
            return cursor.fetchall()

    def update_query_2_results(self, rows):
        self.clear_treeview()
        cols = ("Service Name", "Total Cost")
        self.results_tree.config(columns=cols)
        for col in cols:
            self.results_tree.heading(col, text=col)
            self.results_tree.column(col, width=200, anchor='center')

        if not rows:
            self.results_tree.insert('', tk.END, values=("לא נמצאו נתונים", ""))
        else:
            for row in rows:
                self.results_tree.insert('', tk.END, values=(row[0], f"{row[1]:.2f}"))
    
    def run_procedure_update_memberships(self):
        self.controller.run_db_task(
            self._run_procedure_from_db,
            on_success=self.on_success_action_proc,
            on_error=self.on_error_action
        )

    def _run_procedure_from_db(self, conn):
        with conn.cursor() as cursor:
            cursor.execute("CALL update_expired_memberships()")
        return "עדכון חברות שפג תוקפן בוצע בהצלחה!"

    def on_success_action_proc(self, message):
        messagebox.showinfo("הצלחה", message)

    def on_error_action(self, error):
        messagebox.showerror("שגיאה", f"שגיאה: {error}")


# --- הרצת האפליקציה ---
if __name__ == "__main__":
    app = GymApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
