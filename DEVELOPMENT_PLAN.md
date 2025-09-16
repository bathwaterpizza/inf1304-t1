# Smart Factory Sensor Monitoring System - Development Plan

## Project Overview
Implementation of a distributed sensor monitoring system for a smart factory using Kafka for message streaming, Docker for containerization, and Python for application development. The system will demonstrate load balancing, fault tolerance, and failover capabilities.

## Architecture Components

### 1. Kafka Cluster (Message Brokers)
- 2+ Kafka broker instances running in separate containers using KRaft mode
- Built-in Raft consensus protocol for leader election and coordination
- Topic: `sensor-data` with multiple partitions and replication

### 2. Sensor Simulators (Producers)
- Multiple Python applications simulating factory sensors
- Generate periodic sensor data (temperature, vibration, energy consumption)
- Send data to Kafka topic `sensor-data`

### 3. Data Processors (Consumers)
- Python applications consuming from Kafka topic
- Belong to same consumer group for load balancing
- Process sensor data and detect anomalies
- Generate alerts when thresholds are exceeded

### 4. Data Storage
- Database or logging system for processed data and alerts
- Could use PostgreSQL or simple file logging

## Technology Stack

### Core Technologies
- **Apache Kafka 3.8+**: Latest version with KRaft mode (no ZooKeeper)
- **Python 3.11+**: Latest stable Python version
- **Docker & Docker Compose**: Latest versions for containerization
- **confluent-kafka-python**: Modern Python Kafka client library

### Python Libraries
- `confluent-kafka`: High-performance Kafka client
- `pydantic`: Data validation and settings management
- `asyncio`: For asynchronous operations where beneficial
- `structlog`: Structured logging
- `psycopg2` or `asyncpg`: PostgreSQL connectivity
- `pytest`: Modern testing framework

## Development Phases

### Phase 1: Infrastructure Setup
**Objective**: Set up the basic Docker and Kafka infrastructure

**Tasks**:
1. Create `docker-compose.yml` with:
   - 2-3 Kafka broker services in KRaft mode
   - Proper cluster formation configuration
   - Network configuration for inter-broker communication
   - Volume mounts for persistence

2. Create environment configuration:
   - `config/kraft.properties` for KRaft mode configuration
   - `config/application.properties` for Python apps
   - Environment variables in docker-compose

3. Create basic project structure:
   ```
   /src
     /producers    # Sensor simulators
     /consumers    # Data processors
     /shared       # Common utilities and models
   /config         # Configuration files
   /scripts        # Utility scripts
   /logs          # Log files
   /docker        # Dockerfiles
   ```

4. Create `Makefile` with common operations:
   - `make setup` - Initialize environment and format Kafka storage
   - `make start` - Start all services
   - `make stop` - Stop all services
   - `make clean` - Clean up containers and volumes
   - `make logs` - View aggregated logs
   - `make test` - Run integration tests

**Git Commit**: "Initial project structure and KRaft Kafka infrastructure" ✅ **COMPLETE**

### Phase 2: Kafka Topic Configuration ✅ **COMPLETE**
**Objective**: Configure Kafka topics with proper partitioning and replication

**Tasks**:
1. Create script to initialize Kafka topics:
   - Topic: `sensor-data` with 3 partitions, replication factor 2 ✅
   - Topic: `alerts` for processed alerts ✅

2. Test Kafka cluster connectivity ✅
3. Verify topic creation and configuration ✅

**Git Commit**: "KRaft Kafka cluster setup and topic configuration" ✅ **COMPLETE**

### Phase 3: Sensor Producers Implementation
**Objective**: Implement sensor simulators that generate realistic data

**Tasks**:
1. Create base sensor class:
   - `src/shared/sensor_model.py` - Data models
   - `src/shared/kafka_producer.py` - Kafka producer wrapper

2. Implement different sensor types:
   - `src/producers/temperature_sensor.py`
   - `src/producers/vibration_sensor.py`
   - `src/producers/energy_sensor.py`

3. Create sensor data generator:
   - JSON format with timestamp, sensor_id, location, readings
   - Configurable data generation intervals
   - Realistic value ranges and anomaly injection

4. Dockerize sensor applications:
   - `docker/Dockerfile.producer`
   - Individual containers for each sensor

5. Configuration management:
   - Use environment variables for Kafka connection
   - Configurable sensor parameters
   - Modern Python practices: type hints, dataclasses, async/await where beneficial

**Git Commit**: "Sensor producer implementations with Docker containers"

### Phase 4: Data Consumer Implementation
**Objective**: Implement data processors that consume and analyze sensor data

**Tasks**:
1. Create base consumer framework:
   - `src/shared/kafka_consumer.py` - Kafka consumer wrapper
   - `src/shared/data_processor.py` - Base processing logic

2. Implement data processors:
   - `src/consumers/anomaly_detector.py` - Detect temperature/vibration anomalies
   - `src/consumers/alert_generator.py` - Generate alerts for threshold violations
   - `src/consumers/data_logger.py` - Log processed data

3. Consumer group configuration:
   - All consumers in same group: `sensor-processors`
   - Automatic partition assignment and rebalancing

4. Data processing logic:
   - Temperature thresholds (e.g., > 80°C = warning, > 100°C = critical)
   - Vibration analysis for equipment health
   - Energy consumption pattern detection

5. Dockerize consumer applications:
   - `docker/Dockerfile.consumer`
   - Multiple consumer instances

**Git Commit**: "Data consumer implementations with processing logic"

### Phase 5: Data Storage and Logging
**Objective**: Implement data persistence and comprehensive logging

**Tasks**:
1. Choose storage solution:
   - PostgreSQL database for structured data
   - File-based logging for debugging

2. Implement data models:
   - `src/shared/database.py` - Database connection and models
   - Tables: sensors, readings, alerts, system_events

3. Add logging infrastructure:
   - Structured logging with correlation IDs
   - Log levels: DEBUG, INFO, WARN, ERROR
   - Log aggregation for monitoring

4. Update docker-compose:
   - Add PostgreSQL service
   - Volume mounts for log files
   - Network connectivity

**Git Commit**: "Data storage and logging infrastructure"

### Phase 6: Monitoring and Observability
**Objective**: Add monitoring capabilities to observe system behavior

**Tasks**:
1. Add metrics collection:
   - Producer metrics: messages sent, errors
   - Consumer metrics: lag, processing time
   - Kafka metrics: partition assignments, rebalancing events

2. Create monitoring dashboard:
   - Simple web interface or log analysis scripts
   - Real-time view of system status

3. Enhanced logging:
   - Consumer group rebalancing events
   - Partition assignment changes
   - Error tracking and recovery

**Git Commit**: "Monitoring and observability features"

### Phase 7: Failure Simulation and Testing
**Objective**: Implement failure scenarios and demonstrate fault tolerance

**Tasks**:
1. Create failure simulation scripts:
   - `scripts/simulate_broker_failure.sh` - Stop/start Kafka brokers
   - `scripts/simulate_consumer_failure.sh` - Stop/start consumers
   - `scripts/simulate_network_partition.sh` - Network isolation

2. Implement graceful shutdown:
   - Signal handlers for clean shutdown
   - Resource cleanup and connection closing

3. Test scenarios:
   - Single broker failure (verify replication works)
   - Consumer failure (verify rebalancing)
   - Network partitions (verify resilience)
   - High load scenarios (verify load balancing)

4. Document test results:
   - Log files showing rebalancing behavior
   - Screenshots or recordings of system behavior
   - Performance metrics under different scenarios

**Git Commit**: "Failure simulation scripts and fault tolerance testing"

### Phase 8: Documentation and Final Polish
**Objective**: Complete documentation and ensure easy deployment

**Tasks**:
1. Create comprehensive README:
   - Architecture overview with diagrams
   - Installation and setup instructions
   - Usage examples and commands
   - Troubleshooting guide

2. Finalize Makefile:
   - All necessary operations
   - Parameter validation
   - Error handling

3. Code documentation:
   - Python docstrings for all classes and functions
   - Inline comments for complex logic
   - Configuration file documentation

4. Create final report:
   - Architecture explanation
   - Implementation details
   - Test results and analysis
   - Known limitations and future improvements

**Git Commit**: "Final documentation and project completion"

## Configuration Strategy

### Environment Variables (docker-compose.yml)
```yaml
environment:
  KAFKA_BROKERS: "kafka1:9092,kafka2:9092,kafka3:9092"
  SENSOR_TOPIC: "sensor-data"
  ALERT_TOPIC: "alerts"
  CONSUMER_GROUP: "sensor-processors"
  DATABASE_URL: "postgresql://user:pass@postgres:5432/factory"
  LOG_LEVEL: "INFO"
```

### Application Properties
- `config/kraft.properties` - KRaft mode specific settings
- `config/sensors.properties` - Sensor simulation parameters
- `config/processors.properties` - Data processing thresholds

## Testing Strategy

### Unit Tests
- Individual component testing
- Mock Kafka producers/consumers
- Data processing logic validation

### Integration Tests
- End-to-end message flow
- Database connectivity
- Container orchestration

### Failure Tests
- Broker failure scenarios
- Consumer failure and rebalancing
- Network partition handling
- High load stress testing

## Deliverables Checklist

- [ ] Complete source code with Python applications
- [ ] Docker Compose file with all services
- [ ] Makefile with operational commands
- [ ] Configuration files (properties and environment)
- [ ] Failure simulation scripts
- [ ] Comprehensive documentation
- [ ] Test logs showing rebalancing behavior
- [ ] Final project report

## Git Workflow

Each phase will result in one or more git commits with clear, descriptive messages. The commit history will show the evolution of the project and make it easy to track progress and revert changes if needed.

## Success Criteria

1. **Fault Tolerance**: System continues operating when individual components fail
2. **Load Balancing**: Work is distributed efficiently among consumers
3. **Scalability**: Easy to add more sensors and processors
4. **Observability**: Clear visibility into system behavior and health
5. **Documentation**: Complete instructions for setup and operation

This plan provides a structured approach to building a robust, distributed sensor monitoring system that meets all the project requirements while demonstrating key distributed systems concepts.