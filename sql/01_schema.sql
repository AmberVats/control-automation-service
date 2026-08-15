-- 01_schema.sql
-- Relational DDL for Control Automation Service

CREATE TABLE IF NOT EXISTS controls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) UNIQUE NOT NULL,
    version VARCHAR(20) NOT NULL DEFAULT '1',
    component VARCHAR(100) NOT NULL,
    description TEXT,
    owner VARCHAR(100) DEFAULT 'product_control_analytics',
    schedule VARCHAR(50),
    config_yaml TEXT NOT NULL,
    config_hash VARCHAR(64) NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS control_runs (
    run_id VARCHAR(36) PRIMARY KEY,
    control_name VARCHAR(100) NOT NULL,
    version VARCHAR(20) NOT NULL,
    config_hash VARCHAR(64) NOT NULL,
    triggered_by VARCHAR(50) NOT NULL DEFAULT 'api',
    as_of_date VARCHAR(20),
    start_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    duration_ms REAL,
    status VARCHAR(20) NOT NULL,
    row_count_in INTEGER DEFAULT 0,
    row_count_out INTEGER DEFAULT 0,
    breach_count INTEGER DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS control_exceptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id VARCHAR(36) NOT NULL REFERENCES control_runs(run_id) ON DELETE CASCADE,
    exception_type VARCHAR(50) NOT NULL,
    key_data TEXT,
    field VARCHAR(100),
    source_val TEXT,
    target_val TEXT,
    difference REAL,
    message TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_runs_ctrl_status ON control_runs (control_name, status);
CREATE INDEX IF NOT EXISTS idx_runs_created ON control_runs (created_at);
CREATE INDEX IF NOT EXISTS idx_exceptions_run_id ON control_exceptions (run_id);
