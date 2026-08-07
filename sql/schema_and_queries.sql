-- ============================================================
-- A/B Test Analysis: Checkout Redesign — SQL
-- Works with SQL / PostgreSQL / MySQL (minor syntax tweaks
-- may be needed for date functions depending on engine)
-- ============================================================

-- ---------- SCHEMA ----------
CREATE TABLE IF NOT EXISTS experiment_data (
    user_id           TEXT PRIMARY KEY,
    session_date      DATE,
    group_name        TEXT,   -- 'group' is a reserved word in some engines, hence group_name
    device            TEXT,
    traffic_source    TEXT,
    time_on_page_sec  NUMERIC,
    converted         INTEGER,
    revenue           NUMERIC
);

-- Load data/experiment_data_clean.csv into this table before running queries
-- (rename the CSV's 'group' column header to 'group_name' on import, or
-- alias it in your import step).
-- Example (SQL CLI):
--   SQL3 ab_test.db
--   .mode csv
--   .import data/experiment_data_clean.csv experiment_data

-- ============================================================
-- BUSINESS QUESTIONS
-- ============================================================

-- Q1. Overall conversion rate by group
SELECT
    group_name,
    COUNT(*)                                    AS users,
    SUM(converted)                              AS conversions,
    ROUND(100.0 * AVG(converted), 2)            AS conversion_rate_pct
FROM experiment_data
GROUP BY group_name;

-- Q2. Sample Ratio Mismatch check: are group sizes close to 50/50?
SELECT
    group_name,
    COUNT(*) AS users,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM experiment_data), 2) AS pct_of_total
FROM experiment_data
GROUP BY group_name;

-- Q3. Conversion rate by group AND device (segment breakdown)
SELECT
    device,
    group_name,
    COUNT(*)                              AS users,
    ROUND(100.0 * AVG(converted), 2)      AS conversion_rate_pct
FROM experiment_data
GROUP BY device, group_name
ORDER BY device, group_name;

-- Q4. Daily conversion rate trend by group (for novelty-effect / stability checks)
SELECT
    session_date,
    group_name,
    ROUND(100.0 * AVG(converted), 2) AS conversion_rate_pct
FROM experiment_data
GROUP BY session_date, group_name
ORDER BY session_date, group_name;

-- Q5. Revenue per user (ARPU) by group
SELECT
    group_name,
    ROUND(AVG(revenue), 2) AS arpu,
    ROUND(SUM(revenue), 2) AS total_revenue
FROM experiment_data
GROUP BY group_name;

-- Q6. Conversion rate by traffic source and group
SELECT
    traffic_source,
    group_name,
    COUNT(*)                          AS users,
    ROUND(100.0 * AVG(converted), 2)  AS conversion_rate_pct
FROM experiment_data
GROUP BY traffic_source, group_name
ORDER BY traffic_source, group_name;

-- Q7. Average time on page by group (secondary UX signal)
SELECT
    group_name,
    ROUND(AVG(time_on_page_sec), 1) AS avg_time_on_page_sec
FROM experiment_data
GROUP BY group_name;

-- Q8. Revenue per user among CONVERTERS ONLY (i.e. average order value --
--     checks whether the redesign changed basket size, not just conversion)
SELECT
    group_name,
    ROUND(AVG(revenue), 2) AS avg_order_value
FROM experiment_data
WHERE converted = 1
GROUP BY group_name;

-- Q9. Mobile-only conversion rate (the segment with the real effect)
SELECT
    group_name,
    COUNT(*)                          AS users,
    ROUND(100.0 * AVG(converted), 2)  AS conversion_rate_pct
FROM experiment_data
WHERE device = 'Mobile'
GROUP BY group_name;

-- Q10. Total experiment sample size and date range (for a report header)
SELECT
    COUNT(*)             AS total_users,
    COUNT(DISTINCT group_name) AS groups,
    MIN(session_date)    AS start_date,
    MAX(session_date)    AS end_date,
    COUNT(DISTINCT session_date) AS days_run
FROM experiment_data;
