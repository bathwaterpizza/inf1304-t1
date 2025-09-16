# Factory Monitoring System - Smart Factory Sensor Monitoring

A distributed sensor monitoring system for smart factories using Apache Kafka, Docker, and Python. This system demonstrates load balancing, fault tolerance, and failover capabilities in a distributed environment.

## Features

- **Kafka Cluster**: Multi-broker setup with KRaft mode (no ZooKeeper)
- **Sensor Simulation**: Multiple sensor types (temperature, vibration, energy)
- **Load Balancing**: Automatic consumer group balancing
- **Fault Tolerance**: Broker and consumer failure handling
- **Real-time Processing**: Stream processing with anomaly detection
- **Data Persistence**: PostgreSQL storage with structured schema
- **Monitoring**: Kafka UI for cluster monitoring

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Sensors       │    │  Kafka Cluster  │    │  Processors     │
│  (Producers)    │───▶│   (3 Brokers)   │───▶│  (Consumers)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   PostgreSQL    │
                       │   (Storage)     │
                       └─────────────────┘
```

## Quick Start

1. **Setup Environment**:
   ```bash
   make setup
   ```

2. **Start System**:
   ```bash
   make start
   ```

3. **Check Status**:
   ```bash
   make status
   make health
   ```

4. **Monitor System**:
   ```bash
   make monitor  # Opens Kafka UI
   ```

5. **View Logs**:
   ```bash
   make logs
   ```

6. **Stop System**:
   ```bash
   make stop
   ```

## Development

### Project Structure
```
├── src/
│   ├── producers/     # Sensor simulators
│   ├── consumers/     # Data processors
│   └── shared/        # Common utilities
├── config/            # Configuration files
├── scripts/           # Utility scripts
├── docker/            # Docker files
└── logs/              # Log files
```

### Environment Configuration

Copy `.env.example` to `.env` and adjust variables as needed:

```bash
cp .env .env.local
```

Key configuration options:
- `KAFKA_BROKERS`: Kafka cluster endpoints
- `POSTGRES_*`: Database configuration
- `*_THRESHOLD`: Alert thresholds for sensors

## Available Commands

```bash
make help          # Show all available commands
make setup         # Initialize environment
make start         # Start all services
make stop          # Stop all services
make clean         # Clean up everything
make logs          # View aggregated logs
make status        # Check service status
make health        # Health check all services
make topics        # Create Kafka topics
make monitor       # Open Kafka UI
```

## System Components

### Kafka Cluster
- 3 brokers running in KRaft mode
- Topic: `sensor-data` (3 partitions, replication factor 2)
- Topic: `alerts` (2 partitions, replication factor 2)

### Sensors (Producers)
- Temperature sensors
- Vibration sensors
- Energy consumption sensors

### Processors (Consumers)
- Anomaly detection
- Alert generation
- Data logging

### Storage
- PostgreSQL database
- Structured schema for sensors, readings, and alerts

## Fault Tolerance Testing

Test scenarios included:
- Broker failure simulation
- Consumer failure and rebalancing
- Network partition handling
- High load stress testing

## Monitoring

- Kafka UI: http://localhost:8080
- Database: PostgreSQL on port 5432
- Logs: Structured JSON logging with correlation IDs

## Development Status

This project is part of a distributed systems course and demonstrates:
- ✅ Kafka cluster setup with KRaft mode
- ✅ Docker containerization
- ✅ Configuration management
- 🚧 Sensor producers (Phase 3)
- 🚧 Data consumers (Phase 4)
- 🚧 Failure simulation (Phase 7)

## License

Educational project for distributed systems learning.