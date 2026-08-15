-- 02_views.sql
-- Analytical views for reporting, governance, and the Citizen Developer framework

-- 1. Full Run History with formatted metrics
CREATE VIEW IF NOT EXISTS v_control_run_history AS
SELECT 
    r.run_id,
    r.control_name,
    r.version,
    r.config_hash,
    r.triggered_by,
    r.as_of_date,
    r.start_time,
    r.end_time,
    r.duration_ms,
    r.status,
    r.row_count_in,
    r.row_count_out,
    r.breach_count,
    r.error_message,
    r.created_at
FROM control_runs r
ORDER BY r.created_at DESC;

-- 2. Recent Exceptions with parent control context
CREATE VIEW IF NOT EXISTS v_recent_exceptions AS
SELECT 
    e.id AS exception_id,
    e.run_id,
    r.control_name,
    r.version,
    r.as_of_date,
    e.exception_type,
    e.key_data,
    e.field,
    e.source_val,
    e.target_val,
    e.difference,
    e.message,
    e.created_at
FROM control_exceptions e
JOIN control_runs r ON e.run_id = r.run_id
ORDER BY e.created_at DESC;

-- 3. Summary metrics per control
CREATE VIEW IF NOT EXISTS v_control_summary AS
SELECT 
    control_name,
    COUNT(*) AS total_runs,
    SUM(CASE WHEN status = 'PASS' THEN 1 ELSE 0 END) AS pass_count,
    SUM(CASE WHEN status = 'BREACH' THEN 1 ELSE 0 END) AS breach_count,
    SUM(CASE WHEN status = 'FAIL' THEN 1 ELSE 0 END) AS fail_count,
    ROUND(AVG(duration_ms), 2) AS avg_duration_ms,
    MAX(created_at) AS last_run_at
FROM control_runs
GROUP BY control_name;
