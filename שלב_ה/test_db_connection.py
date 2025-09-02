import psycopg2
from psycopg2 import Error
import datetime

# פרטי החיבור
conn_params = {
    "user": "yehuda",
    "password": "ninga",
    "host": "localhost",
    "port": "5432",
    "database": "gym_db"
}

try:
    # התחברות לבסיס הנתונים
    conn = psycopg2.connect(**conn_params)
    cursor = conn.cursor()

    # הפעלת הפרוצדורה ישירות
    print("מנסה להפעיל את הפרוצדורה...")
    
    # הגדרת הפרמטרים. כעת ה-CAST יטפל בהכל.
    p_pid = 123456789
    p_firstname = 'Test'
    p_lastname = 'User'
    p_dateofb = '1990-01-01'  # שליחת תאריך כמחרוזת
    p_email = 'test@example.com'
    p_address = 'Tel Aviv'
    p_phone = '0501234567'  # שליחת מספר כמחרוזת
    p_membership_type = 'Monthly'
    p_is_active = True
    
    # הקריאה לפרוצדורה עם המרת סוגים מפורשת ב-SQL
    cursor.execute(
        f"CALL register_new_member(%s::integer, %s::character varying, %s::character varying, %s::date, %s::character varying, %s::character varying, %s::numeric, %s::character varying, %s::boolean)",
        (p_pid, p_firstname, p_lastname, p_dateofb, p_email, p_address, p_phone, p_membership_type, p_is_active)
    )
    
    conn.commit()
    print("הצלחה! חבר נרשם בהצלחה.")

except (Exception, Error) as error:
    print("אירעה שגיאה:")
    print(error)

finally:
    if conn:
        cursor.close()
        conn.close()
        print("החיבור לבסיס הנתונים נסגר.")