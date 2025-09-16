-- Factory Monitoring System Database Schema
-- This script initializes the PostgreSQL database with necessary tables

-- Enable UUID extension for generating unique IDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Sensors table to store sensor metadata
CREATE TABLE sensors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sensor_id VARCHAR(50) UNIQUE NOT NULL,
    sensor_type VARCHAR(20) NOT NULL CHECK (sensor_type IN ('temperature', 'vibration', 'energy')),
    location VARCHAR(100) NOT NULL,
    sector VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'maintenance')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Sensor readings table to store raw sensor data
CREATE TABLE sensor_readings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sensor_id VARCHAR(50) NOT NULL,
    timestamp_utc TIMESTAMP WITH TIME ZONE NOT NULL,
    reading_value DECIMAL(10,4) NOT NULL,
    unit VARCHAR(20) NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sensor_id) REFERENCES sensors(sensor_id)
);

-- Alerts table to store processed alerts
CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sensor_id VARCHAR(50) NOT NULL,
    alert_type VARCHAR(20) NOT NULL CHECK (alert_type IN ('warning', 'critical')),
    message TEXT NOT NULL,
    reading_value DECIMAL(10,4) NOT NULL,
    threshold_value DECIMAL(10,4) NOT NULL,
    timestamp_utc TIMESTAMP WITH TIME ZONE NOT NULL,
    resolved_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'resolved', 'acknowledged')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sensor_id) REFERENCES sensors(sensor_id)
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
CREATE INDEX idx_alerts_sensor_id ON alerts(sensor_id);
CREATE INDEX idx_alerts_timestamp ON alerts(timestamp_utc);
CREATE INDEX idx_alerts_status ON alerts(status);
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

-- Insert sample sensor data
INSERT INTO sensors (sensor_id, sensor_type, location, sector) VALUES
('TEMP_001', 'temperature', 'Production Line A', 'manufacturing'),
('TEMP_002', 'temperature', 'Production Line B', 'manufacturing'),
('VIB_001', 'vibration', 'Motor Assembly 1', 'manufacturing'),
('VIB_002', 'vibration', 'Motor Assembly 2', 'manufacturing'),
('ENERGY_001', 'energy', 'Main Power Distribution', 'utilities'),
('ENERGY_002', 'energy', 'HVAC System', 'utilities');

-- Create views for common queries
CREATE VIEW active_alerts AS
SELECT 
    a.*,
    s.sensor_type,
    s.location,
    s.sector
FROM alerts a
JOIN sensors s ON a.sensor_id = s.sensor_id
WHERE a.status = 'active';

CREATE VIEW sensor_summary AS
SELECT 
    s.sensor_id,
    s.sensor_type,
    s.location,
    s.sector,
    s.status,
    COUNT(sr.id) as total_readings,
    MAX(sr.timestamp_utc) as last_reading,
    COUNT(a.id) FILTER (WHERE a.status = 'active') as active_alerts
FROM sensors s
LEFT JOIN sensor_readings sr ON s.sensor_id = sr.sensor_id
LEFT JOIN alerts a ON s.sensor_id = a.sensor_id
GROUP BY s.id, s.sensor_id, s.sensor_type, s.location, s.sector, s.status;