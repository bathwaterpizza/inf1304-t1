# Factory Monitoring System 🏭

A distributed sensor monitoring system for smart factories using **Apache Kafka**, **Docker**, and **Python**. This project implements a scalable IoT data processing pipeline following modern distributed systems patterns.

## 🎯 Project Overview

This system simulates and monitors sensor data from a smart factory environment, processing real-time data streams to detect anomalies and generate alerts. The architecture demonstrates key distributed systems concepts including:

- **Event-driven architecture** with Apache Kafka
- **Containerized microservices** with Docker
- **Real-time data processing** and anomaly detection
- **Scalable producer-consumer patterns**
- **Load balancing** and automatic failover
- **Real-time monitoring** and observability
- **Fault tolerance** demonstration

## 🏗️ Architecture

```mermaid
graph TB
    subgraph "Sensor Producers"
        SP1[Temperature Sensor]
        SP2[Vibration Sensor] 
        SP3[Energy Sensor]
    end
    
    subgraph "Kafka Cluster"
        K1[Kafka Broker 1]
        K2[Kafka Broker 2]
        K3[Kafka Broker 3]
        UI[Kafka UI]
    end
    
    subgraph "Data Consumers"
        C1[Consumer 1]
        C2[Consumer 2]
        C3[Consumer 3]
    end
    
    subgraph "Storage & Monitoring"
        PG[PostgreSQL]
        MS[Monitoring Service<br/>Backend]
    end
    
    %% Each producer can connect to all Kafka brokers
    SP1 --> K1
    SP1 --> K2
    SP1 --> K3
    SP2 --> K1
    SP2 --> K2
    SP2 --> K3
    SP3 --> K1
    SP3 --> K2
    SP3 --> K3
    
    %% Each consumer can connect to all Kafka brokers
    C1 --> K1
    C1 --> K2
    C1 --> K3
    C2 --> K1
    C2 --> K2
    C2 --> K3
    C3 --> K1
    C3 --> K2
    C3 --> K3
    
    %% Each consumer writes to PostgreSQL
    C1 --> PG
    C2 --> PG
    C3 --> PG
    
    %% Monitoring service reads from PostgreSQL
    MS --> PG
```

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose v2
- Make (for convenience commands)
- Python 3.11+ (for local development)

### 1. Quick Start - Everything at Once

```bash
# Build and start complete system (recommended for first-time users)
make all

# Open monitoring dashboard (http://localhost:5000)
make dashboard

# Open Kafka UI (http://localhost:8080)
make monitor
```

### 2. Step-by-Step Setup

```bash
# Start infrastructure only
make start

# Start sensor producers
make start-producers

# Start data consumers
make start-consumers

# Start monitoring dashboard
make start-monitoring
```

### 3. Alternative Startup Options

```bash
# Infrastructure + producers only (no consumers)
make infrastructure-only

# Infrastructure + producers + consumers (no monitoring)
make with-consumers

# Complete system with monitoring
make with-monitoring
```

### 4. Monitor Real-time Data

```bash
# View producer logs
make logs-producers

# View consumer logs  
make logs-consumers

# Monitor sensor data stream
make monitor-sensors

# Monitor alerts
make monitor-alerts

# Open monitoring dashboard (http://localhost:5000)
make dashboard

# Open Kafka UI (http://localhost:8080)
make monitor
```

## 📊 System Components

### Sensor Producers

**Single Unified Producer** (`src/producers/sensor_producer.py`):
- **Environment-driven configuration**: Change sensor type via `SENSOR_TYPE` env var
- **Multiple sensor types**: temperature, vibration, energy, humidity, pressure
- **Realistic data simulation**: Time-based patterns, noise, anomalies
- **Alert generation**: Automatic warning/critical threshold detection
- **Configurable sampling**: Different intervals per sensor type
- **Health monitoring**: Reports status to monitoring database

### Data Consumers

**Single Unified Consumer** (`src/consumers/sensor_consumer.py`):
- **Load balancing**: Automatic partition assignment within consumer group
- **Anomaly detection**: Real-time threshold-based alert generation
- **Generic processing**: Handles all sensor types in same codebase
- **Fault tolerance**: Automatic rebalancing when consumers join/leave
- **Health monitoring**: Reports status and partition assignments to monitoring database
- **Data persistence**: Stores processed data and alerts in PostgreSQL

### Kafka Infrastructure

**3-Node KRaft Cluster**:
- **Modern Kafka**: No ZooKeeper dependency (KRaft mode)
- **High availability**: 3 brokers with replication factor 2
- **Topics**: `sensor-data` (3 partitions), `alerts` (2 partitions)
- **External access**: Ports 9092, 9094, 9096
- **Load distribution**: Any producer can send to any broker, any broker can route to any consumer

### Monitoring & Observability

**Real-time Monitoring Dashboard** (`src/monitoring/monitoring_service.py`):
- **Flask Backend**: REST API providing real-time system metrics
- **Web Frontend**: Responsive dashboard with auto-refresh
- **System Health**: Consumer/producer status and heartbeat monitoring
- **Partition Tracking**: Real-time partition assignment visualization
- **Rebalancing Events**: Live monitoring of consumer rebalancing
- **Performance Metrics**: Throughput and processing statistics
- **Fault Tolerance Demo**: Visual demonstration of system resilience

### Data Storage

- **PostgreSQL 15**: Processed data, alerts, and monitoring information
- **Kafka UI**: Real-time cluster monitoring (port 8080)
- **Monitoring Dashboard**: System observability (port 5000)

## 🛠️ Development Commands

| Command | Description |
|---------|-------------|
| **Quick Start** |
| `make all` | **Build and start complete system (infrastructure + producers + consumers + monitoring)** |
| `make help` | Show all available commands |
| `make setup` | Initialize environment and format Kafka storage |
| **Infrastructure Management** |
| `make start` | Start infrastructure services only (Kafka + PostgreSQL + Kafka UI) |
| `make infrastructure-only` | Start infrastructure + producers (no consumers, no monitoring) |
| `make with-consumers` | Start infrastructure + producers + consumers (no monitoring) |
| `make with-monitoring` | Start complete system with monitoring dashboard |
| `make stop` | Stop all services |
| `make clean` | Remove containers and volumes |
| `make status` | Check service status |
| `make health` | Check service health |
| **Component Management** |
| `make build-all` | Build all Docker images |
| `make build-producers` | Build sensor producer images |
| `make build-consumers` | Build consumer images |
| `make start-producers` | Start sensor producers |
| `make stop-producers` | Stop sensor producers |
| `make start-consumers` | Start consumer instances |
| `make stop-consumers` | Stop consumer instances |
| `make start-monitoring` | Start monitoring dashboard |
| **Monitoring & Debugging** |
| `make logs-producers` | View sensor producer logs |
| `make logs-consumers` | View consumer logs |
| `make monitor-sensors` | Monitor real-time sensor data |
| `make monitor-alerts` | Monitor alerts in real-time |
| `make dashboard` | Open monitoring dashboard in browser |
| `make monitor` | Open Kafka UI |
| **Testing & Verification** |
| `make test-external` | Test external connectivity |
| `make verify-cluster` | Comprehensive cluster verification |

## ⚙️ Configuration

### Sensor Configuration

Each sensor type has predefined realistic ranges and thresholds:

```python
sensor_configs = {
    "temperature": {
        "base_value": 25.0,      # °C
        "warning_threshold": 35.0,
        "critical_threshold": 40.0,
        "sampling_interval": 3.0  # seconds
    },
    "vibration": {
        "base_value": 2.0,       # mm/s  
        "warning_threshold": 5.0,
        "critical_threshold": 7.0,
        "sampling_interval": 4.0
    },
    "energy": {
        "base_value": 100.0,     # kW
        "warning_threshold": 150.0, 
        "critical_threshold": 180.0,
        "sampling_interval": 10.0
    }
}
```

### Environment Variables

```bash
# Sensor Configuration
SENSOR_ID=temp-sensor-001
SENSOR_TYPE=temperature
SAMPLING_INTERVAL=3.0
FACTORY_SECTION=production
MACHINE_ID=machine-001
ZONE=zone-a

# Consumer Configuration
CONSUMER_ID=consumer-001
CONSUMER_GROUP=sensor-processors

# Kafka Configuration  
KAFKA_BROKERS=kafka1:29092,kafka2:29092,kafka3:29092
SENSOR_TOPIC=sensor-data
ALERT_TOPIC=alerts

# Database Configuration
DATABASE_URL=postgresql://factory_user:factory_pass@postgres:5432/factory_monitoring

# Monitoring Configuration
MONITORING_HOST=0.0.0.0
MONITORING_PORT=5000
```

### Example Sensor Data

```json
{
  "timestamp": "2025-09-16T21:41:41.011144Z",
  "sensor_id": "temp-sensor-001",
  "sensor_type": "temperature", 
  "location": {
    "factory_section": "production",
    "machine_id": "machine-001",
    "zone": "zone-a"
  },
  "value": 42.48,
  "unit": "°C",
  "alert_level": "critical",
  "quality": 1.0,
  "metadata": {
    "reading_count": 14,
    "warning_threshold": 35.0,
    "critical_threshold": 40.0
  }
}
```

## 📈 Data Flow & Alert System

### Load Balancing & Fault Tolerance
1. **Producer Distribution**: Any sensor can send data to any Kafka broker
2. **Consumer Load Balancing**: Kafka automatically distributes partitions among available consumers
3. **Automatic Rebalancing**: When consumers join/leave, partitions are automatically reassigned
4. **Health Monitoring**: Real-time tracking of producer/consumer health and status
5. **Failover Demonstration**: Kill containers to see system adapt and recover

### Alert Levels
- **Normal**: Value within expected range
- **Warning**: 15% probability, value near warning threshold  
- **Critical**: 5% probability, value near/above critical threshold

### Real-time Processing
1. Sensors generate readings every 3-10 seconds
2. Data published to Kafka `sensor-data` topic (load balanced across brokers)
3. Consumers process data for anomaly detection (load balanced via partition assignment)
4. Alerts generated for threshold violations and published to `alerts` topic
5. Processed data and metadata stored in PostgreSQL
6. Monitoring dashboard provides real-time visibility into system behavior

### Monitoring Features
- **System Status**: Real-time health of all producers and consumers
- **Partition Assignments**: Live view of which consumers are handling which partitions
- **Rebalancing Events**: Visual demonstration of Kafka's fault tolerance
- **Performance Metrics**: Throughput, processing rates, and system statistics
- **Alert Tracking**: Real-time display of anomaly detection and alert generation

## 🔧 Monitoring & Observability

### Real-time Dashboard
Access the monitoring dashboard at **http://localhost:5000**

**Features**:
- **System Status**: Live health indicators for all components
- **Consumer Health**: Real-time consumer status with partition assignments
- **Producer Health**: Producer connection status and message rates
- **Rebalancing Events**: Live visualization of Kafka consumer rebalancing
- **Performance Metrics**: Throughput statistics and system performance
- **Fault Tolerance Demo**: Visual demonstration of system resilience

**API Endpoints**:
- `GET /api/system-status` - Overall system health overview
- `GET /api/consumer-health` - Consumer status and partition assignments
- `GET /api/producer-health` - Producer status and message rates
- `GET /api/partition-assignment` - Current partition assignments and activity
- `GET /api/real-time-metrics` - Real-time throughput metrics
- `GET /api/recent-alerts` - Recent anomaly alerts and rebalancing events

### Fault Tolerance Testing

**Start complete system with monitoring**:
```bash
make all
```

**Test consumer failure** (watch rebalancing in dashboard):
```bash
# Kill a consumer and watch partition reassignment
docker kill consumer-1
```

**Test producer failure** (watch health status change):
```bash
# Kill a producer and watch health indicators
docker kill temperature-sensor
```

**Monitor rebalancing events in real-time**:
```bash
# View rebalancing events as they happen
make monitor-alerts
```

### Database Schema

The monitoring system uses enhanced PostgreSQL schema:
- `consumer_health`: Consumer status, heartbeats, partition assignments
- `producer_health`: Producer status, heartbeats, message rates
- `rebalancing_events`: Real-time rebalancing event tracking
- `sensor_readings`: Processed sensor data with metadata
- `alerts`: Generated alerts and anomaly detection results

## 🧪 Testing & Verification

```bash
# Test Kafka connectivity
make test-external

# Test topic operations
make test-topics

# Comprehensive cluster verification
make verify-cluster

# Monitor specific sensor type
docker compose logs -f temperature-sensor

# Test fault tolerance - kill a consumer and watch rebalancing
docker kill consumer-1
make dashboard  # Watch partition reassignment in real-time

# Test producer failure - kill a sensor and watch health status
docker kill vibration-sensor  
make dashboard  # Watch producer health change

# Monitor rebalancing events in real-time
make monitor-alerts
```

## 📂 Project Structure

```
.
├── src/
│   ├── producers/
│   │   └── sensor_producer.py      # Unified sensor simulator
│   ├── consumers/
│   │   └── sensor_consumer.py      # Unified data processor  
│   └── monitoring/
│       ├── monitoring_service.py   # Flask backend API
│       └── templates/
│           └── dashboard.html      # Real-time web dashboard
├── docker/
│   ├── Dockerfile.producer         # Sensor container image
│   ├── Dockerfile.consumer         # Consumer container image
│   └── Dockerfile.tester           # Testing utilities
├── Dockerfile.monitoring           # Monitoring service image
├── docker-compose.yml              # Multi-service orchestration
├── Makefile                        # Development commands
├── requirements.txt                # Python dependencies
└── README.md                       # This file
```

## 🎯 Development Phases

- [x] **Phase 1**: Infrastructure Setup (Kafka KRaft + PostgreSQL)
- [x] **Phase 2**: Topic Configuration & Verification  
- [x] **Phase 3**: Sensor Producers Implementation
- [x] **Phase 4**: Data Consumers & Processing
- [x] **Phase 5**: Data Storage & Database Integration
- [x] **Phase 6**: Monitoring & Observability (Real-time Dashboard)
- [ ] **Phase 7**: Failure Simulation & Testing
- [ ] **Phase 8**: Performance Optimization & Documentation

## 🚀 Next Steps

1. **Implement Failure Simulation Scripts**: Automated testing of fault tolerance scenarios
2. **Performance Optimization**: Load testing and horizontal scaling strategies
3. **Advanced Analytics**: Machine learning-based anomaly detection
4. **Alert System Enhancement**: Email/SMS notifications for critical alerts
5. **Metrics Export**: Prometheus/Grafana integration for advanced monitoring

## 🤝 Contributing

This is an educational project for distributed systems learning. Feel free to:
- Experiment with different sensor configurations
- Add new sensor types
- Implement consumer patterns
- Optimize performance

## 📄 License

Educational project - feel free to use for learning purposes.