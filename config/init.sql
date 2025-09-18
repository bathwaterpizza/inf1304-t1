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

-- Indexes for performance optimization
CREATE INDEX idx_sensor_readings_sensor_id ON sensor_readings(sensor_id);
CREATE INDEX idx_sensor_readings_timestamp ON sensor_readings(timestamp_utc);
CREATE INDEX idx_sensor_readings_sensor_type ON sensor_readings(sensor_type);
CREATE INDEX idx_sensor_readings_alert_level ON sensor_readings(alert_level);
CREATE INDEX idx_alerts_sensor_id ON alerts(sensor_id);
CREATE INDEX idx_alerts_timestamp ON alerts(timestamp_utc);
CREATE INDEX idx_alerts_status ON alerts(status);
CREATE INDEX idx_alerts_severity ON alerts(severity);
CREATE INDEX idx_alerts_anomaly_type ON alerts(anomaly_type);
CREATE INDEX idx_system_events_timestamp ON system_events(timestamp_utc);
CREATE INDEX idx_system_events_component ON system_events(component);

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
    sr.created_at
FROM sensor_readings sr
JOIN sensors s ON sr.sensor_id = s.sensor_id
WHERE sr.timestamp_utc >= NOW() - INTERVAL '1 hour'
ORDER BY sr.timestamp_utc DESC;