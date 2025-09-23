# Phase 6: Monitoring and Observability

This phase implements comprehensive monitoring and observability for the Factory Monitoring System, providing real-time visibility into system health, load balancing, and fault tolerance.

## Features

### 🎯 Real-time System Monitoring
- **Consumer Health Tracking**: Monitor active consumers, partition assignments, and message processing rates
- **Producer Health Monitoring**: Track producer status, message send rates, and connection health
- **System Status Overview**: Real-time view of all system components and their health status

### 🔄 Kafka Rebalancing Visualization
- **Partition Assignment Tracking**: See which consumers are assigned to which partitions
- **Rebalancing Event Monitoring**: Track when consumer rebalancing occurs
- **Load Distribution Analysis**: Visualize how load is distributed across consumers

### 📊 Performance Metrics
- **Throughput Monitoring**: Track message processing and production rates
- **Processing Latency**: Monitor end-to-end message processing times
- **Alert Generation**: Track anomaly detection and alert generation rates

### 🛡️ Fault Tolerance Demonstration
- **Real-time Rebalancing**: See system automatically rebalance when containers are killed
- **Health Recovery**: Monitor how the system recovers from failures
- **Load Redistribution**: Visualize how load gets redistributed during failures

## Architecture

### Database Schema Enhancements
Enhanced PostgreSQL schema to track:
- Consumer health and heartbeats
- Producer health and status
- Kafka partition assignments
- Rebalancing events
- Message processing metadata

### Monitoring Service Components
1. **Flask API Service** (`src/monitoring/monitoring_service.py`)
   - REST API endpoints for system metrics
   - Database connection pooling
   - Real-time data aggregation

2. **Frontend Dashboard** (`src/monitoring/templates/dashboard.html`)
   - Real-time web interface
   - Auto-refreshing charts and metrics
   - Responsive design for monitoring

3. **Enhanced Consumers** (modified existing consumers)
   - Rebalancing callbacks to track partition assignments
   - Health status reporting to database
   - Kafka metadata extraction for processing tracking

4. **Enhanced Producers** (modified existing producers)
   - Health status reporting to database
   - Message send rate tracking
   - Connection status monitoring

## API Endpoints

### System Status
- `GET /api/system-status` - Overall system health overview
- `GET /api/consumer-health` - Consumer status and assignments
- `GET /api/producer-health` - Producer status and rates
- `GET /api/partition-assignment` - Current partition assignments

### Metrics & Analytics
- `GET /api/real-time-metrics` - Real-time throughput metrics
- `GET /api/recent-alerts` - Recent anomaly alerts

## Usage

### Starting the Complete System with Monitoring

```bash
# Start the complete system including monitoring dashboard
make full-stack

# Or start monitoring separately
make start-monitoring

# Open the dashboard
make dashboard
```

### Accessing the Dashboard

The monitoring dashboard is available at: **http://localhost:5000**

### Testing Fault Tolerance

1. Start the complete system:
   ```bash
   make full-stack
   ```

2. Open the monitoring dashboard in your browser

3. Kill some consumer containers to see rebalancing:
   ```bash
   # Kill a consumer container
   docker kill sensor-consumer-1
   
   # Or kill a producer
   docker kill temperature-sensor
   ```

4. Watch the dashboard to see:
   - Rebalancing events being logged
   - Partition assignments changing
   - Load being redistributed to remaining consumers
   - System recovering and returning to normal operation

### Monitoring Features

#### Real-time Visualizations
- **System Status**: Live status of all producers and consumers
- **Consumer Health**: Individual consumer status with partition assignments
- **Producer Health**: Producer connection status and send rates
- **Partition Activity**: Message distribution across Kafka partitions
- **Recent Alerts**: Latest anomaly detections and alerts
- **Rebalancing Events**: Real-time consumer rebalancing activity

#### Automatic Refresh
- Dashboard auto-refreshes every 5 seconds
- Real-time updates without manual refresh
- Error handling for network issues

## Database Schema

### New Tables Added

```sql
-- Consumer health tracking
CREATE TABLE consumer_health (
    consumer_id VARCHAR(255) PRIMARY KEY,
    status VARCHAR(50) NOT NULL,
    last_heartbeat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_partitions INTEGER[],
    messages_processed_last_minute INTEGER DEFAULT 0
);

-- Producer health tracking  
CREATE TABLE producer_health (
    producer_id VARCHAR(255) PRIMARY KEY,
    sensor_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL,
    last_heartbeat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    messages_sent_last_minute INTEGER DEFAULT 0
);

-- Rebalancing event tracking
CREATE TABLE rebalancing_events (
    id SERIAL PRIMARY KEY,
    consumer_id VARCHAR(255) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    partition_number INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Enhanced Existing Tables

```sql
-- Added to sensor_readings table
ALTER TABLE sensor_readings ADD COLUMN processed_by_consumer VARCHAR(255);
ALTER TABLE sensor_readings ADD COLUMN kafka_partition INTEGER;
ALTER TABLE sensor_readings ADD COLUMN kafka_offset BIGINT;
ALTER TABLE sensor_readings ADD COLUMN processing_timestamp TIMESTAMP;
```

## Configuration

### Environment Variables
- `DATABASE_URL`: PostgreSQL connection string
- `MONITORING_HOST`: Host for monitoring service (default: 0.0.0.0)
- `MONITORING_PORT`: Port for monitoring service (default: 5000)
- `FLASK_ENV`: Flask environment (development/production)

### Docker Configuration
The monitoring service is configured in `docker-compose.yml`:
- Runs on port 5000
- Depends on PostgreSQL
- Auto-restart on failure
- Health checks enabled

## Demonstration Scenarios

### 1. Normal Operation Monitoring
- Start system and observe normal operation
- Monitor message flow through producers → Kafka → consumers
- Track processing rates and system health

### 2. Consumer Failure Simulation
```bash
# Kill a consumer and watch rebalancing
docker kill sensor-consumer-1
# Observe partition reassignment and load redistribution
```

### 3. Producer Failure Simulation
```bash
# Kill a producer and watch health status
docker kill temperature-sensor  
# Observe producer health change and alert generation
```

### 4. Kafka Broker Failure (Advanced)
```bash
# Kill a Kafka broker
docker kill kafka2
# Observe system resilience and recovery
```

### 5. Database Monitoring
- Monitor processing latency
- Track alert generation patterns
- Analyze message distribution

## Troubleshooting

### Common Issues
1. **Dashboard not loading**: Check if monitoring service is running
2. **No data displayed**: Verify database connection and that sensors are running
3. **Rebalancing not showing**: Ensure consumers are configured with database connection

### Debugging Commands
```bash
# Check monitoring service logs
docker logs monitoring

# Check database connectivity
docker exec -it monitoring python -c "
from src.monitoring.monitoring_service import get_db_connection
print('DB connection:', get_db_connection())
"

# Monitor database directly
docker exec -it postgres psql -U factory_user -d factory_monitoring -c "
SELECT * FROM consumer_health ORDER BY last_heartbeat DESC;
"
```

## Benefits

### For Development
- **Real-time Debugging**: See system behavior in real-time
- **Performance Analysis**: Identify bottlenecks and optimization opportunities
- **Fault Testing**: Safely test fault tolerance scenarios

### for Operations  
- **System Health Monitoring**: Continuous visibility into system status
- **Proactive Issue Detection**: Early warning of potential problems
- **Capacity Planning**: Understanding of system load and capacity

### For Demonstration
- **Visual System Behavior**: Clear visualization of distributed system concepts
- **Fault Tolerance Demo**: Concrete demonstration of system resilience
- **Educational Value**: Hands-on learning about distributed systems

This monitoring system provides comprehensive observability into the distributed factory monitoring system, enabling real-time visualization of system behavior, fault tolerance, and load balancing in action.