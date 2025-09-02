-- אינדקסים idempotent (לא יכשלו אם כבר קיימים)
CREATE INDEX IF NOT EXISTS idx_shift_date         ON shift(date);
CREATE INDEX IF NOT EXISTS idx_shift_pid_date     ON shift(pid, date);
CREATE INDEX IF NOT EXISTS idx_serves_servicename ON serves(servicename);

-- עדכון סטטיסטיקות לאופטימיזציית שאילתות
ANALYZE shift;
ANALYZE serves;
