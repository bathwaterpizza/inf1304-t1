-- Factory Monitoring System Database Schema
-- This script initializes the PostgreSQL database with necessary tables

-- Enable UUID extension for generating unique IDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Sensors table to store sensor metadata
CREATE TABLE sensors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sensor_id VARCHAR(50) UNIQUE NOT NULL,
    sensor_type VARCHAR(20) NOT NULL CHECK (sensor_type IN ('temperature', 'vibration', 'energy', 'humidity', 'pressure')),
    location JSONB NOT NULL, -- Store complete location structure
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'maintenance')),
    metadata JSONB, -- Additional sensor configuration and thresholds
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Sensor readings table to store raw sensor data
CREATE TABLE sensor_readings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sensor_id VARCHAR(50) NOT NULL,
    timestamp_utc TIMESTAMP WITH TIME ZONE NOT NULL,
    sensor_type VARCHAR(20) NOT NULL,
    reading_value DECIMAL(12,4) NOT NULL,
    unit VARCHAR(20) NOT NULL,
    alert_level VARCHAR(20) NOT NULL CHECK (alert_level IN ('normal', 'warning', 'critical')),
    quality DECIMAL(3,2) DEFAULT 1.0,
    location JSONB NOT NULL,
    metadata JSONB,
    -- Processing tracking fields
    processed_by_consumer VARCHAR(50), -- Which consumer processed this message
    kafka_partition INTEGER, -- Which Kafka partition this came from
    kafka_offset BIGINT, -- Kafka message offset
    processing_timestamp TIMESTAMP WITH TIME ZONE, -- When consumer processed this
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sensor_id) REFERENCES sensors(sensor_id) ON DELETE CASCADE
);

-- Alerts table to store generated alerts and anomalies
CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    alert_id VARCHAR(100) UNIQUE NOT NULL, -- External alert ID from consumer
    sensor_id VARCHAR(50) NOT NULL,
    sensor_type VARCHAR(20) NOT NULL,
    anomaly_type VARCHAR(50) NOT NULL, -- Type of detected anomaly
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    sensor_value DECIMAL(12,4) NOT NULL,
    sensor_unit VARCHAR(20) NOT NULL,
    sensor_alert_level VARCHAR(20) NOT NULL CHECK (sensor_alert_level IN ('normal', 'warning', 'critical')),
    description TEXT NOT NULL,
    location JSONB NOT NULL,
    detected_by VARCHAR(50) NOT NULL, -- Consumer ID that detected the anomaly
    timestamp_utc TIMESTAMP WITH TIME ZONE NOT NULL,
    resolved_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'resolved', 'acknowledged')),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sensor_id) REFERENCES sensors(sensor_id) ON DELETE CASCADE
);

-- System events table for tracking system behavior
CREATE TABLE system_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type VARCHAR(50) NOT NULL,
    component VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    metadata JSONB,
    timestamp_utc TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Consumer health tracking table
CREATE TABLE consumer_health (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    consumer_id VARCHAR(50) UNIQUE NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('active', 'inactive', 'error')),
    assigned_partitions JSONB, -- Array of partition numbers assigned to this consumer
    last_heartbeat TIMESTAMP WITH TIME ZONE NOT NULL,
    messages_processed_last_minute INTEGER DEFAULT 0,
    total_messages_processed BIGINT DEFAULT 0,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Producer health tracking table
CREATE TABLE producer_health (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    producer_id VARCHAR(50) UNIQUE NOT NULL, -- sensor_id acts as producer_id
    sensor_type VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('active', 'inactive', 'error')),
    last_heartbeat TIMESTAMP WITH TIME ZONE NOT NULL,
    messages_sent_last_minute INTEGER DEFAULT 0,
    total_messages_sent BIGINT DEFAULT 0,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Rebalancing events tracking table
CREATE TABLE rebalancing_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type VARCHAR(50) NOT NULL CHECK (event_type IN ('rebalance_start', 'rebalance_complete', 'partition_assigned', 'partition_revoked')),
    consumer_id VARCHAR(50) NOT NULL,
    partition_number INTEGER,
    topic_name VARCHAR(100) NOT NULL,
    timestamp_utc TIMESTAMP WITH TIME ZONE NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to automatically update updated_at column
CREATE TRIGGER update_sensors_updated_at 
    BEFORE UPDATE ON sensors 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_consumer_health_updated_at 
    BEFORE UPDATE ON consumer_health 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_producer_health_updated_at 
    BEFORE UPDATE ON producer_health 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Insert sample sensor data matching our actual running sensors
INSERT INTO sensors (sensor_id, sensor_type, location, metadata) VALUES
('temp-sensor-001', 'temperature', '{"factory_section": "production", "machine_id": "machine-001", "zone": "zone-a"}', '{"warning_threshold": 35.0, "critical_threshold": 40.0, "unit": "°C"}'),
('vib-sensor-002', 'vibration', '{"factory_section": "production", "machine_id": "machine-002", "zone": "zone-b"}', '{"warning_threshold": 5.0, "critical_threshold": 7.0, "unit": "mm/s"}'),
('energy-sensor-003', 'energy', '{"factory_section": "utilities", "machine_id": "generator-001", "zone": "zone-c"}', '{"warning_threshold": 150.0, "critical_threshold": 180.0, "unit": "kW"}');

-- Create views for common queries
CREATE VIEW active_alerts AS
SELECT 
    a.id,
    a.alert_id,
    a.sensor_id,
    a.sensor_type,
    a.anomaly_type,
    a.severity,
    a.sensor_value,
    a.sensor_unit,
    a.sensor_alert_level,
    a.description,
    a.location,
    a.detected_by,
    a.timestamp_utc,
    a.resolved_at,
    a.status,
    a.metadata,
    a.created_at
FROM alerts a
JOIN sensors s ON a.sensor_id = s.sensor_id
WHERE a.status = 'active';

CREATE VIEW sensor_summary AS
SELECT 
    s.sensor_id,
    s.sensor_type,
    s.location,
    s.status,
    COUNT(sr.id) as total_readings,
    MAX(sr.timestamp_utc) as last_reading,
    COUNT(CASE WHEN sr.alert_level = 'warning' THEN 1 END) as warning_readings,
    COUNT(CASE WHEN sr.alert_level = 'critical' THEN 1 END) as critical_readings,
    COUNT(a.id) FILTER (WHERE a.status = 'active') as active_alerts
FROM sensors s
LEFT JOIN sensor_readings sr ON s.sensor_id = sr.sensor_id
LEFT JOIN alerts a ON s.sensor_id = a.sensor_id
GROUP BY s.id, s.sensor_id, s.sensor_type, s.location, s.status;

CREATE VIEW recent_readings AS
SELECT 
    sr.id,
    sr.sensor_id,
    sr.timestamp_utc,
    sr.sensor_type,
    sr.reading_value,
    sr.unit,
    sr.alert_level,
    sr.quality,
    sr.location,
    sr.metadata,
    sr.processed_by_consumer,
    sr.kafka_partition,
    sr.kafka_offset,
    sr.processing_timestamp,
    sr.created_at
FROM sensor_readings sr
JOIN sensors s ON sr.sensor_id = s.sensor_id
WHERE sr.timestamp_utc >= NOW() - INTERVAL '1 hour'
ORDER BY sr.timestamp_utc DESC;

-- Real-time metrics view for monitoring dashboard
CREATE VIEW real_time_metrics AS
SELECT 
    'consumer_throughput' as metric_type,
    processed_by_consumer as component_id,
    COUNT(*) as value,
    DATE_TRUNC('minute', processing_timestamp) as time_bucket
FROM sensor_readings 
WHERE processing_timestamp >= NOW() - INTERVAL '10 minutes'
AND processed_by_consumer IS NOT NULL
GROUP BY processed_by_consumer, DATE_TRUNC('minute', processing_timestamp)

UNION ALL

SELECT 
    'producer_throughput' as metric_type,
    sensor_id as component_id,
    COUNT(*) as value,
    DATE_TRUNC('minute', timestamp_utc) as time_bucket
FROM sensor_readings 
WHERE timestamp_utc >= NOW() - INTERVAL '10 minutes'
GROUP BY sensor_id, DATE_TRUNC('minute', timestamp_utc)

UNION ALL

SELECT 
    'partition_distribution' as metric_type,
    CONCAT('partition-', kafka_partition::text) as component_id,
    COUNT(*) as value,
    DATE_TRUNC('minute', processing_timestamp) as time_bucket
FROM sensor_readings 
WHERE processing_timestamp >= NOW() - INTERVAL '10 minutes'
AND kafka_partition IS NOT NULL
GROUP BY kafka_partition, DATE_TRUNC('minute', processing_timestamp)

ORDER BY time_bucket DESC, metric_type, component_id;

-- Current system status view
CREATE VIEW system_status AS
SELECT 
    'consumers' as component_type,
    COUNT(CASE WHEN status = 'active' THEN 1 END) as active_count,
    COUNT(CASE WHEN status = 'inactive' THEN 1 END) as inactive_count,
    COUNT(*) as total_count,
    MAX(last_heartbeat) as last_activity
FROM consumer_health
WHERE last_heartbeat >= NOW() - INTERVAL '2 minutes'

UNION ALL

SELECT 
    'producers' as component_type,
    COUNT(CASE WHEN status = 'active' THEN 1 END) as active_count,
    COUNT(CASE WHEN status = 'inactive' THEN 1 END) as inactive_count,
    COUNT(*) as total_count,
    MAX(last_heartbeat) as last_activity
FROM producer_health
WHERE last_heartbeat >= NOW() - INTERVAL '2 minutes';