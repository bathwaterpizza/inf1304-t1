# Smart Factory Sensor Monitoring System - Development Plan

## Project Overview
Implementation of a distributed sensor monitoring system for a smart factory using Kafka for message streaming, Docker for containerization, and Python for application development. The system will demonstrate load balancing, fault tolerance, and failover capabilities.

## Architecture Components

### 1. Kafka Cluster (Message Brokers)
- 2+ Kafka broker instances running in separate containers using KRaft mode
- Built-in Raft consensus protocol for leader election and coordination
- Topic: `sensor-data` with multiple partitions and replication

### 2. Sensor Simulators (Producers)
- Single unified Python application (`sensor_producer.py`) that simulates factory sensors
- Environment-driven configuration to determine sensor type (temperature, vibration, energy)
- Multiple container instances (3 sensors) using the same codebase with different configurations
- Generate periodic sensor data with realistic patterns and anomaly injection
- Send data to Kafka topic `sensor-data`

### 3. Data Processors (Consumers)
- Single unified Python application (`sensor_consumer.py`) that processes sensor data
- Environment-driven configuration for different processing behaviors
- Multiple container instances for load balancing and fault tolerance
- Belong to same consumer group for automatic load distribution
- Process sensor data, detect anomalies, and generate alerts

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
- `python-dotenv`: Environment variable management (minimal dependencies)
- Standard library: `json`, `logging`, `asyncio`, `random`, `time`

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
     /producers    # Single unified sensor simulator
     /consumers    # Single unified data processor
   /config         # Configuration files
   /scripts        # Utility scripts
   /logs          # Log files
   /docker        # Dockerfiles
   ```

4. Create `Makefile` with common operations:
   - `make setup` - Initialize environment and format Kafka storage
   - `make start` - Start infrastructure only
   - `make full-start` - Start infrastructure + sensors
   - `make build-sensors` - Build sensor images
   - `make start-sensors` - Start sensor producers  
   - `make stop-sensors` - Stop sensor producers
   - `make logs-sensors` - View sensor logs
   - `make monitor-sensors` - Monitor real-time data
   - `make stop` - Stop all services
   - `make clean` - Clean up containers and volumes

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

### Phase 3: Sensor Producers Implementation ✅ **COMPLETE**
**Objective**: Implement unified sensor simulator that generates realistic data

**Tasks**:
1. Create unified sensor producer: ✅
   - `src/producers/sensor_producer.py` - Single sensor simulator class
   - Environment-driven configuration (SENSOR_TYPE, SENSOR_ID, etc.)
   - Support for multiple sensor types: temperature, vibration, energy, humidity, pressure

2. Sensor data generation: ✅
   - JSON format with timestamp, sensor_id, location, readings, alert_level
   - Configurable sampling intervals per sensor type
   - Realistic value ranges with time-based variations and noise
   - Alert generation: 15% warning probability, 5% critical probability

3. Containerization: ✅
   - `docker/Dockerfile.producer` - Single Dockerfile for all sensor types
   - Docker Compose configuration for 3 sensor instances
   - Environment variable configuration for different sensor types

4. Configuration management: ✅
   - Environment variables for Kafka connection and sensor parameters
   - Realistic sensor configurations with thresholds
   - Clean logging and error handling

**Git Commit**: "Unified sensor producer with environment-driven configuration" ✅ **COMPLETE**

### Phase 4: Data Consumer Implementation ✅ **COMPLETE**
**Objective**: Implement unified data processor that consumes and analyzes sensor data

**Tasks**:
1. Create unified consumer framework: ✅
   - `src/consumers/sensor_consumer.py` - Single consumer application
   - Environment-driven configuration for different processing modes
   - Handle all sensor types in one codebase

2. Implement data processing capabilities: ✅
   - Real-time anomaly detection for all sensor types
   - Alert generation and escalation logic
   - Data aggregation and statistical analysis
   - Configurable processing thresholds per sensor type

3. Consumer group configuration: ✅
   - All consumer instances in same group: `sensor-processors`
   - Automatic partition assignment and load balancing
   - Graceful rebalancing when consumers join/leave

4. Data processing logic: ✅
   - Process sensor data based on sensor_type field
   - Generate alerts for threshold violations (warning/critical)
   - Log processed data and system events
   - Handle different sensor patterns and anomaly detection

5. Containerization: ✅
   - `docker/Dockerfile.consumer` - Single Dockerfile for all consumers
   - Multiple consumer instances for load balancing
   - Environment variable configuration

**Git Commit**: "Unified data consumer with load balancing and anomaly detection" ✅ **COMPLETE**

### Phase 5: Data Storage and Logging ✅ **COMPLETE**
**Objective**: Implement data persistence and comprehensive logging

**Tasks**:
1. Integrate PostgreSQL database: ✅
   - Use existing PostgreSQL service from docker-compose
   - Comprehensive database schema for processed data
   - Connection management in consumer application

2. Implement data storage: ✅
   - Store processed sensor readings
   - Store generated alerts and system events
   - Advanced SQL operations with indexing and optimization

3. Enhanced logging: ✅
   - Structured logging with timestamps and correlation
   - Consumer group rebalancing events
   - Processing metrics and error tracking
   - Log aggregation for monitoring

4. Update docker-compose: ✅
   - Volume mounts for persistent storage
   - Environment variables for database connection
   - Health checks for database connectivity

**Git Commit**: "Data storage integration and enhanced logging" ✅ **COMPLETE**

### Phase 6: Monitoring and Observability ✅ **COMPLETE**
**Objective**: Add comprehensive monitoring capabilities to observe system behavior

**Tasks**:
1. Add metrics collection: ✅
   - Producer metrics: messages sent, errors, health status
   - Consumer metrics: lag, processing time, partition assignments
   - Kafka metrics: partition assignments, rebalancing events

2. Create monitoring dashboard: ✅
   - Flask-based REST API service providing real-time metrics
   - Responsive web interface with auto-refresh
   - Real-time view of system status and health

3. Enhanced logging: ✅
   - Consumer group rebalancing events
   - Partition assignment changes
   - Error tracking and recovery
   - Database schema for monitoring data

4. Monitoring features implemented: ✅
   - System status overview with health indicators
   - Consumer health tracking with partition assignments
   - Producer health monitoring with connection status
   - Real-time rebalancing event visualization
   - Performance metrics and throughput tracking
   - Alert generation monitoring

**Git Commit**: "Monitoring and observability features" ✅ **COMPLETE**

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
# Sensor Producer Configuration
environment:
  SENSOR_ID: "temp-sensor-001"
  SENSOR_TYPE: "temperature"  # or "vibration", "energy"
  KAFKA_BROKERS: "kafka1:29092,kafka2:29092,kafka3:29092"
  SENSOR_TOPIC: "sensor-data"
  SAMPLING_INTERVAL: "3.0"
  FACTORY_SECTION: "production"
  MACHINE_ID: "machine-001"
  ZONE: "zone-a"

# Consumer Configuration  
environment:
  KAFKA_BROKERS: "kafka1:29092,kafka2:29092,kafka3:29092"
  SENSOR_TOPIC: "sensor-data"
  ALERT_TOPIC: "alerts"
  CONSUMER_GROUP: "sensor-processors"
  DATABASE_URL: "postgresql://factory_user:factory_pass@postgres:5432/factory_monitoring"
  LOG_LEVEL: "INFO"
```

### Simplified Configuration
- **No separate config files needed** - Environment variables handle all configuration
- **Single codebase approach** - Same code, different environment variables
- **Container-based scaling** - Multiple instances of same application

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

- [x] **Infrastructure**: KRaft Kafka cluster with 3 brokers
- [x] **Docker Compose**: Multi-service orchestration file
- [x] **Sensor Producer**: Unified sensor simulator with environment config  
- [x] **Containerization**: Docker setup for sensor producers
- [x] **Makefile**: Comprehensive operational commands
- [x] **Documentation**: Updated README and architecture docs
- [x] **Data Consumer**: Unified data processor with anomaly detection
- [x] **Data Storage**: PostgreSQL integration for processed data
- [x] **Monitoring**: Real-time monitoring dashboard with comprehensive observability
- [x] **Health Tracking**: Producer and consumer health monitoring
- [x] **Fault Tolerance**: Visual demonstration of system resilience and rebalancing
- [ ] **Failure Simulation**: Scripts for testing fault tolerance
- [ ] **Integration Tests**: End-to-end testing scenarios
- [ ] **Final Report**: Complete project documentation

**Current Status**: Phase 6 Complete ✅ - Ready for Phase 7 (Failure Simulation and Testing)

## Git Workflow

Each phase will result in one or more git commits with clear, descriptive messages. The commit history will show the evolution of the project and make it easy to track progress and revert changes if needed.

## Success Criteria

1. **Fault Tolerance**: System continues operating when individual components fail
2. **Load Balancing**: Work is distributed efficiently among consumers
3. **Scalability**: Easy to add more sensors and processors
4. **Observability**: Clear visibility into system behavior and health
5. **Documentation**: Complete instructions for setup and operation

This plan provides a structured approach to building a robust, distributed sensor monitoring system that meets all the project requirements while demonstrating key distributed systems concepts.