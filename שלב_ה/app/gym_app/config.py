
# -*- coding: utf-8 -*-
"""
config.py - הגדרות ואילוצים ניתנים לשינוי בלי לגעת בקוד הלוגיקה
"""
from dataclasses import dataclass

# App title for the main window
APP_TITLE = "Gym Management System"


@dataclass(frozen=True)
class DBConfig:
    host: str = "localhost"
    port: int = 5432
    dbname: str = "gym_db"
    user: str = "yehuda"
    password: str = "ninga"
    minconn: int = 1
    maxconn: int = 6

# מיפוי שמות טבלאות/עמודות כדי להתאים לסכימה שונה בקלות
TABLES = {
    "person": "person",
    "member": "member",
    "shift": "shift",
    "serves": "serves",
}

COLUMNS = {
    # person
    "person.pid": "pid",
    "person.firstname": "firstname",
    "person.lastname": "lastname",
    "person.dateofb": "dateofb",
    "person.email": "email",
    "person.address": "address",
    "person.phone": "phone",

    # member
    "member.personid": "personid",
    "member.membershiptype": "membershiptype",
    "member.memberstartdate": "memberstartdate",
    "member.memberenddate": "memberenddate",  # עשוי להיות חסר אצלך, לא חובה
    "member.isactive": "isactive",

    # shift
    "shift.pid": "pid",
    "shift.date": "date",                # אם אין עמודת date – נשתמש ב-clock_in בשאילתות
    "shift.clock_in": "clock_in",
    "shift.clock_out": "clock_out",

    # serves
    "serves.servicename": "servicename",
    "serves.price": "price",
}

# הגדרות UI
PAGE_SIZE = 50  # כמה רשומות בעמוד ב-Treeview
THEME = "clam"  # ל-macOS נוח ל-styling
