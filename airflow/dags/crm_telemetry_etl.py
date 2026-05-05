from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from clickhouse_driver import Client
import logging
import pandas as pd
import os
import numpy as np

logger = logging.getLogger(__name__)

# Пути к CSV файлам
CRM_CSV_PATH = '/opt/airflow/data/crm_data.csv'
TELEMETRY_CSV_PATH = '/opt/airflow/data/telemetry_data.csv'

# Конфигурация ClickHouse
CLICKHOUSE_CONFIG = {
    'host': 'clickhouse',
    'port': 9000,
    'user': 'default',
    'password': '',
    'database': 'default'
}

def convert_numpy_types(obj):
    """Рекурсивное преобразование numpy типов в Python native типы"""
    if isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, pd.Timestamp):
        return obj.to_pydatetime()
    elif isinstance(obj, (datetime, pd.Timestamp)):
        return obj
    elif isinstance(obj, dict):
        return {k: convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_numpy_types(item) for item in obj]
    return obj

def load_crm_to_clickhouse(**context):
    """Загрузка CRM данных из CSV напрямую в ClickHouse"""

    if not os.path.exists(CRM_CSV_PATH):
        raise FileNotFoundError(f"CRM CSV file not found: {CRM_CSV_PATH}")

    # Читаем CSV с указанием типов
    df = pd.read_csv(CRM_CSV_PATH, parse_dates=['registration_date'])
    logger.info(f"Read {len(df)} CRM records from CSV")

    # Подключаемся к ClickHouse
    client = Client(**CLICKHOUSE_CONFIG)

    try:
        # Очищаем таблицу перед загрузкой
        client.execute("TRUNCATE TABLE IF EXISTS crm_customers_raw")

        # Конвертируем DataFrame в список кортежей с правильными типами
        data = []
        for _, row in df.iterrows():
            # Преобразуем каждый элемент в Python native тип
            record = (
                int(row['customer_id']),  # UInt64
                str(row['customer_name']),  # String
                str(row['email']),  # String
                str(row['phone']),  # String
                row['registration_date'].to_pydatetime() if pd.notna(row['registration_date']) else None,  # Date
                str(row['customer_segment'])  # String
            )
            data.append(record)

        # Вставляем данные порциями по 1000 записей
        batch_size = 1000
        for i in range(0, len(data), batch_size):
            batch = data[i:i+batch_size]
            client.execute(
                "INSERT INTO crm_customers_raw (customer_id, customer_name, email, phone, registration_date, customer_segment) VALUES",
                batch
            )
            logger.info(f"Loaded batch {i//batch_size + 1}: {len(batch)} records")

        logger.info(f"Successfully loaded {len(data)} CRM records to ClickHouse")

        # Выводим пример данных для проверки
        sample = client.execute("SELECT * FROM crm_customers_raw LIMIT 3")
        logger.info(f"Sample data in ClickHouse: {sample}")

    except Exception as e:
        logger.error(f"Error loading CRM data to ClickHouse: {e}")
        logger.error(f"Data sample: {data[:2] if 'data' in locals() else 'No data'}")
        raise
    finally:
        client.disconnect()

def load_telemetry_to_clickhouse(**context):
    """Загрузка телеметрии из CSV напрямую в ClickHouse"""

    if not os.path.exists(TELEMETRY_CSV_PATH):
        raise FileNotFoundError(f"Telemetry CSV file not found: {TELEMETRY_CSV_PATH}")

    # Читаем CSV с парсингом даты
    df = pd.read_csv(TELEMETRY_CSV_PATH, parse_dates=['event_timestamp'])
    logger.info(f"Read {len(df)} telemetry records from CSV")

    # Подключаемся к ClickHouse
    client = Client(**CLICKHOUSE_CONFIG)

    try:
        # Очищаем таблицу перед загрузкой
        client.execute("TRUNCATE TABLE IF EXISTS telemetry_raw")

        # Конвертируем DataFrame в список кортежей с правильными типами
        data = []
        for _, row in df.iterrows():
            # Проверяем и конвертируем типы
            event_id = int(row['event_id']) if pd.notna(row['event_id']) else 0
            customer_id = int(row['customer_id']) if pd.notna(row['customer_id']) else 0
            event_type = str(row['event_type']) if pd.notna(row['event_type']) else 'unknown'
            event_timestamp = row['event_timestamp'].to_pydatetime() if pd.notna(row['event_timestamp']) else datetime.now()
            device_id = str(row['device_id']) if pd.notna(row['device_id']) else 'unknown'
            session_duration = int(row['session_duration_seconds']) if pd.notna(row['session_duration_seconds']) else 0
            page_views = int(row['page_views']) if pd.notna(row['page_views']) else 0
            actions_count = int(row['actions_count']) if pd.notna(row['actions_count']) else 0

            record = (
                event_id,
                customer_id,
                event_type,
                event_timestamp,
                device_id,
                session_duration,
                page_views,
                actions_count
            )
            data.append(record)

        # Вставляем данные порциями
        batch_size = 1000
        for i in range(0, len(data), batch_size):
            batch = data[i:i+batch_size]
            client.execute(
                "INSERT INTO telemetry_raw (event_id, customer_id, event_type, event_timestamp, device_id, session_duration_seconds, page_views, actions_count) VALUES",
                batch
            )
            logger.info(f"Loaded batch {i//batch_size + 1}: {len(batch)} records")

        logger.info(f"Successfully loaded {len(data)} telemetry records to ClickHouse")

        # Выводим статистику
        stats = client.execute("""
                               SELECT
                                   count(*) as total_events,
                                   countDistinct(customer_id) as unique_customers,
                                   min(event_timestamp) as first_event,
                                   max(event_timestamp) as last_event
                               FROM telemetry_raw
                               """)

        logger.info(f"Telemetry stats in ClickHouse: total_events={stats[0][0]}, "
                    f"unique_customers={stats[0][1]}, "
                    f"period={stats[0][2]} - {stats[0][3]}")

    except Exception as e:
        logger.error(f"Error loading telemetry data to ClickHouse: {e}")
        logger.error(f"Data sample: {data[:2] if 'data' in locals() else 'No data'}")
        raise
    finally:
        client.disconnect()

def update_customer_telemetry_mart(**context):
    """Обновление витрины данных в ClickHouse - максимально упрощенная версия"""
    client = Client(**CLICKHOUSE_CONFIG)

    try:
        # Очищаем витрину
        client.execute("TRUNCATE TABLE IF EXISTS customer_telemetry_mart")

        # Заполняем витрину базовыми агрегатами без сложных формул
        query = """
                INSERT INTO customer_telemetry_mart
                SELECT
                    c.customer_id,
                    any(c.customer_name) AS customer_name,
                    any(c.customer_segment) AS customer_segment,
                    any(c.registration_date) AS registration_date,
                    countDistinct(t.event_id) AS total_sessions,
                    sum(t.session_duration_seconds) AS total_session_duration_seconds,
                    avg(t.session_duration_seconds) AS avg_session_duration_seconds,
                    sum(t.page_views) AS total_page_views,
                    sum(t.actions_count) AS total_actions,
                    sum(t.actions_count) / countDistinct(t.event_id) AS avg_actions_per_session,
                    min(toDate(t.event_timestamp)) AS first_event_date,
                    max(toDate(t.event_timestamp)) AS last_event_date,
                    dateDiff('day', max(toDate(t.event_timestamp)), today()) AS days_since_last_event,
                    0.0 AS engagement_score,
                    'Unknown' AS churn_risk,
                    now() AS updated_at
                FROM telemetry_raw t
                    INNER JOIN crm_customers_raw c ON t.customer_id = c.customer_id
                GROUP BY c.customer_id \
                """

        client.execute(query)

        # Обновляем engagement_score отдельным запросом
        client.execute("""
                       ALTER TABLE customer_telemetry_mart UPDATE
                           engagement_score = (log(total_sessions + 1) * 10 +
                           (avg_session_duration_seconds / 60) +
                           log(total_actions + 1) * 5),
                           churn_risk = multiIf(
                           days_since_last_event > 30, 'High',
                           days_since_last_event > 14, 'Medium',
                           'Low'
                           )
                           WHERE 1=1
                       """)

        logger.info("Customer Telemetry Mart updated successfully")

        # Выводим статистику
        stats = client.execute("SELECT count(*) FROM customer_telemetry_mart")
        logger.info(f"Total customers in mart: {stats[0][0]}")

    except Exception as e:
        logger.error(f"Error updating mart: {e}")
        raise
    finally:
        client.disconnect()

def validate_mart_data(**context):
    """Валидация данных в витрине"""
    client = Client(**CLICKHOUSE_CONFIG)

    try:
        # Проверка на аномалии
        anomalies = client.execute("""
                                   SELECT
                                       countIf(customer_name = '') as empty_names,
                                       countIf(total_sessions = 0) as zero_sessions,
                                       countIf(engagement_score < 0 or engagement_score > 100) as invalid_scores,
                                       countIf(days_since_last_event < 0) as negative_days
                                   FROM customer_telemetry_mart
                                   """)

        a = anomalies[0]
        logger.info("=== Data Validation Report ===")
        logger.info(f"Empty customer names: {a[0]}")
        logger.info(f"Customers with zero sessions: {a[1]}")
        logger.info(f"Invalid engagement scores: {a[2]}")
        logger.info(f"Negative days since last event: {a[3]}")

        # Проверка распределения churn risk
        distribution = client.execute("""
                                      SELECT
                                          churn_risk,
                                          count(*) as count,
                round(avg(engagement_score), 2) as avg_score
                                      FROM customer_telemetry_mart
                                      GROUP BY churn_risk
                                      ORDER BY churn_risk
                                      """)

        logger.info("Churn risk distribution:")
        for row in distribution:
            logger.info(f"  {row[0]}: {row[1]} customers, avg engagement={row[2]}")

    except Exception as e:
        logger.error(f"Error validating mart: {e}")
        raise
    finally:
        client.disconnect()

def generate_report(**context):
    """Генерация итогового отчета"""
    client = Client(**CLICKHOUSE_CONFIG)

    try:
        # Сводная статистика по витрине
        report = client.execute("""
                                WITH summary AS (
                                    SELECT
                                        customer_segment,
                                        count(*) as customers_count,
                                        round(avg(engagement_score), 2) as avg_engagement,
                                        round(avg(total_actions), 1) as avg_actions,
                                        round(avg(total_session_duration_seconds) / 60, 1) as avg_minutes_spent,
                                        countIf(churn_risk = 'High') as high_risk_count
                                    FROM customer_telemetry_mart
                                    GROUP BY customer_segment
                                )
                                SELECT *
                                FROM summary
                                ORDER BY avg_engagement DESC
                                """)

        logger.info("=== FINAL REPORT: Customer Telemetry Analytics ===")
        logger.info(f"{'Segment':<15} {'Customers':<10} {'Engagement':<12} {'Actions':<10} {'Minutes':<10} {'High Risk':<10}")
        logger.info("-" * 70)

        for row in report:
            logger.info(f"{row[0]:<15} {row[1]:<10} {row[2]:<12} {row[3]:<10} {row[4]:<10} {row[5]:<10}")

        # Общая статистика
        total_stats = client.execute("""
                                     SELECT
                                         count(*) as total_customers,
                                         round(avg(engagement_score), 2) as avg_engagement,
                                         countIf(churn_risk = 'Low') as low_risk,
                                         countIf(churn_risk = 'Medium') as medium_risk,
                                         countIf(churn_risk = 'High') as high_risk
                                     FROM customer_telemetry_mart
                                     """)

        t = total_stats[0]
        logger.info("-" * 70)
        logger.info(f"TOTAL: {t[0]} customers, Avg Engagement: {t[1]}")
        logger.info(f"Risk Distribution: Low={t[2]}, Medium={t[3]}, High={t[4]}")

    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise
    finally:
        client.disconnect()

# DAG definition
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 11, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5)
}

with DAG(
        'crm_telemetry_etl',
        default_args=default_args,
        description='ETL: Load CRM and Telemetry from CSV to ClickHouse, build customer analytics mart',
        schedule_interval='@daily',
        catchup=False,
        tags=['crm', 'telemetry', 'clickhouse', 'etl', 'analytics']
) as dag:

    load_crm = PythonOperator(
        task_id='load_crm_to_clickhouse',
        python_callable=load_crm_to_clickhouse,
        provide_context=True
    )

    load_telemetry = PythonOperator(
        task_id='load_telemetry_to_clickhouse',
        python_callable=load_telemetry_to_clickhouse,
        provide_context=True
    )

    update_mart = PythonOperator(
        task_id='update_customer_mart',
        python_callable=update_customer_telemetry_mart,
        provide_context=True
    )

    validate = PythonOperator(
        task_id='validate_mart_data',
        python_callable=validate_mart_data,
        provide_context=True
    )

    report = PythonOperator(
        task_id='generate_final_report',
        python_callable=generate_report,
        provide_context=True
    )

    # Зависимости
    [load_crm, load_telemetry] >> update_mart >> validate >> report