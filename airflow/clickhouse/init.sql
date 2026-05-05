-- Создание таблицы для сырых данных CRM
CREATE TABLE IF NOT EXISTS crm_customers_raw (
                                                 customer_id UInt64,
                                                 customer_name String,
                                                 email String,
                                                 phone String,
                                                 registration_date Date,
                                                 customer_segment String,
                                                 _loaded_at DateTime DEFAULT now()
    ) ENGINE = MergeTree()
    ORDER BY (customer_id, registration_date);

-- Создание таблицы для сырых данных телеметрии
CREATE TABLE IF NOT EXISTS telemetry_raw (
                                             event_id UInt64,
                                             customer_id UInt64,
                                             event_type String,
                                             event_timestamp DateTime,
                                             device_id String,
                                             session_duration_seconds UInt32,
                                             page_views UInt32,
                                             actions_count UInt32,
                                             _loaded_at DateTime DEFAULT now()
    ) ENGINE = MergeTree()
    ORDER BY (customer_id, event_timestamp);

-- Создание витрины данных для сервиса отчетов
CREATE TABLE IF NOT EXISTS customer_telemetry_mart (
                                                       customer_id UInt64,
                                                       customer_name String,
                                                       customer_segment String,
                                                       registration_date Date,

    -- Телеметрические метрики
                                                       total_sessions UInt64,
                                                       total_session_duration_seconds UInt64,
                                                       avg_session_duration_seconds Float64,
                                                       total_page_views UInt64,
                                                       total_actions UInt64,
                                                       avg_actions_per_session Float64,

    -- Временные метрики
                                                       first_event_date Date,
                                                       last_event_date Date,
                                                       days_since_last_event UInt32,

    -- Производные метрики
                                                       engagement_score Float64,
                                                       churn_risk String,

    -- Служебные поля
                                                       updated_at DateTime DEFAULT now()
    ) ENGINE = ReplacingMergeTree(updated_at)
    ORDER BY (customer_id)
    SETTINGS index_granularity = 8192;