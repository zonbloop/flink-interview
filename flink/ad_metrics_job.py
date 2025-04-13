from pyflink.datastream import StreamExecutionEnvironment
from pyflink.table import StreamTableEnvironment, EnvironmentSettings
from pyflink.table.catalog import ObjectPath
from pyflink.common import Configuration

def main():
    # Fault tolerant
    config = Configuration()
    config.set_string("state.backend", "rocksdb")
    config.set_string("state.checkpoints.dir", "file:///tmp/flink-checkpoints")
    config.set_string("state.savepoints.dir", "file:///tmp/flink-savepoints")
    # Set up the environment
    env = StreamExecutionEnvironment.get_execution_environment(config)
    env.set_parallelism(2)

    env_settings = EnvironmentSettings.in_streaming_mode()
    table_env = StreamTableEnvironment.create(env, environment_settings=env_settings)

    kafka_bootstrap = 'kafka:9092'

    # ---- Source: Ad Impressions ----
    table_env.execute_sql("""
        CREATE TABLE IF NOT EXISTS ad_impressions (
            impression_id STRING,
            user_id STRING,
            campaign_id STRING,
            ad_id STRING,
            device_type STRING,
            browser STRING,
            event_timestamp BIGINT,
            cost DOUBLE,
            event_time AS TO_TIMESTAMP_LTZ(event_timestamp, 3),
            WATERMARK FOR event_time AS event_time - INTERVAL '5' SECOND
        ) WITH (
            'connector' = 'kafka',
            'topic' = 'ad-impressions',
            'properties.bootstrap.servers' = 'kafka:9092',
            'format' = 'json',
            'scan.startup.mode' = 'earliest-offset'
        )
    """)

    # ---- Source: Ad Clicks ----
    table_env.execute_sql("""
        CREATE TABLE IF NOT EXISTS ad_clicks (
            click_id STRING,
            impression_id STRING,
            user_id STRING,
            event_timestamp BIGINT,
            event_time AS TO_TIMESTAMP_LTZ(event_timestamp, 3),
            WATERMARK FOR event_time AS event_time - INTERVAL '5' SECOND
        ) WITH (
            'connector' = 'kafka',
            'topic' = 'ad-clicks',
            'properties.bootstrap.servers' = 'kafka:9092',
            'format' = 'json',
            'scan.startup.mode' = 'earliest-offset'
        )
    """)

    # ---- Safe Drop: CTR Sink Table ----
    catalog = table_env.get_catalog(table_env.get_current_catalog())

    # Drop ctr_by_campaign if it exists
    ctr_table_path = ObjectPath(table_env.get_current_database(), "ctr_by_campaign")
    if catalog.table_exists(ctr_table_path):
        catalog.drop_table(ctr_table_path, True)

    # Drop engagement_by_device if it exists
    engagement_table_path = ObjectPath(table_env.get_current_database(), "engagement_by_device")
    if catalog.table_exists(engagement_table_path):
        catalog.drop_table(engagement_table_path, True)

    # ---- Sink: CTR by Campaign to PostgreSQL ----
    table_env.execute_sql("""
        CREATE TABLE ctr_by_campaign (
            campaign_id STRING,
            window_start TIMESTAMP(3),
            window_end TIMESTAMP(3),
            impressions BIGINT,
            clicks BIGINT,
            ctr DOUBLE
        ) WITH (
            'connector' = 'jdbc',
            'url' = 'jdbc:postgresql://postgres:5432/ad_analytics',
            'table-name' = 'ctr_by_campaign',
            'driver' = 'org.postgresql.Driver',
            'username' = 'superset',
            'password' = 'superset'
        )
    """)

    # ---- Sink: Engagement to PostgreSQL ----
    table_env.execute_sql("""
        CREATE TABLE engagement_by_device (
            device_type STRING,
            window_start TIMESTAMP(3),
            window_end TIMESTAMP(3),
            impressions BIGINT,
            clicks BIGINT
        ) WITH (
            'connector' = 'jdbc',
            'url' = 'jdbc:postgresql://postgres:5432/ad_analytics',
            'table-name' = 'engagement_by_device',
            'driver' = 'org.postgresql.Driver',
            'username' = 'superset',
            'password' = 'superset'
        )
    """)


    stmt_set = table_env.create_statement_set()

    stmt_set.add_insert_sql("""
        INSERT INTO ctr_by_campaign
        SELECT
            i.campaign_id,
            TUMBLE_START(i.event_time, INTERVAL '1' MINUTE),
            TUMBLE_END(i.event_time, INTERVAL '1' MINUTE),
            COUNT(DISTINCT i.impression_id),
            COUNT(DISTINCT c.click_id),
            CASE
            WHEN COUNT(DISTINCT i.impression_id) = 0 THEN 0
            ELSE CAST(COUNT(DISTINCT c.click_id) AS DOUBLE) / COUNT(DISTINCT i.impression_id)
            END AS ctr
        FROM ad_impressions i
        LEFT JOIN ad_clicks c ON i.impression_id = c.impression_id
        GROUP BY TUMBLE(i.event_time, INTERVAL '1' MINUTE), i.campaign_id
    """)

    stmt_set.add_insert_sql("""
        INSERT INTO engagement_by_device
        SELECT
            i.device_type,
            TUMBLE_START(i.event_time, INTERVAL '1' MINUTE),
            TUMBLE_END(i.event_time, INTERVAL '1' MINUTE),
            COUNT(DISTINCT i.impression_id),
            COUNT(DISTINCT c.click_id)
        FROM ad_impressions i
        LEFT JOIN ad_clicks c ON i.impression_id = c.impression_id
        GROUP BY TUMBLE(i.event_time, INTERVAL '1' MINUTE), i.device_type
    """)

    stmt_set.execute()


if __name__ == '__main__':
    main()
