import re
import pandas as pd

sql_file_path = "backup_452025.sql"

with open(sql_file_path, "r", encoding="utf-8") as f:
    sql_text = f.read()
    
# חילוץ הגדרות טבלאות מהקובץ
table_defs = re.findall(r"CREATE TABLE .*?;\n", sql_text, re.DOTALL)

print(f"נמצאו {len(table_defs)} טבלאות")

# הצגת שמות הטבלאות
for i, table in enumerate(table_defs, 1):
    match = re.search(r'CREATE TABLE\s+\w+\."?(\w+)"?', table)
    if match:
        print(f"{i}. {match.group(1)}")
    else:
        print(f"{i}. שם טבלה לא נמצא")

print("\n--- מבנה כל טבלה ---\n")

for table in table_defs:
    match = re.search(r'CREATE TABLE\s+\w+\."?(\w+)"?', table)
    if match:
        table_name = match.group(1)
        print(f"\n🧱 טבלה: {table_name}")
        
        # חילוץ שורות העמודות מתוך התוכן שבין הסוגריים
        columns_section = re.search(r'\((.*?)\)', table, re.DOTALL)
        if columns_section:
            columns = columns_section.group(1).split(',\n')
            for col in columns:
                col = col.strip()
                col_match = re.match(r'"?(\w+)"?\s+([\w\(\)]+)', col)
                if col_match:
                    col_name, col_type = col_match.groups()
                    print(f"  - {col_name}: {col_type}")
