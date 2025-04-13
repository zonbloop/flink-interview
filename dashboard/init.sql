CREATE TABLE IF NOT EXISTS engagement_by_device (
    device_type VARCHAR,
    window_start TIMESTAMP,
    window_end TIMESTAMP,
    impressions BIGINT,
    clicks BIGINT
);

CREATE TABLE IF NOT EXISTS ctr_by_campaign (
    campaign_id VARCHAR,
    window_start TIMESTAMP,
    window_end TIMESTAMP,
    impressions BIGINT,
    clicks BIGINT,
    ctr FLOAT
);
