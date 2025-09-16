# Makefile for Factory Monitoring System
# This file provides convenient commands for managing the distributed system

.PHONY: help setup start stop clean status topics health test logs verify-cluster test-connectivity test-topics test-external
	@docker compose exec kafka2 kafka-broker-api-versions --bootstrap-server localhost:9094 > /dev/null 2>&1 && echo "✓ Kafka2: Healthy" || echo "✗ Kafka2: Unhealthy"
	@docker compose exec kafka3 kafka-broker-api-versions --bootstrap-server localhost:9096 > /dev/null 2>&1 && echo "✓ Kafka3: Healthy" || echo "✗ Kafka3: Unhealthy"
	@echo ""
	@echo "PostgreSQL:"
	@docker compose exec postgres pg_isready -U factory_user > /dev/null 2>&1 && echo "✓ PostgreSQL: Healthy" || echo "✗ PostgreSQL: Unhealthy"tem

.PHONY: help setup start stop clean logs test status topics health build-sensors start-sensors stop-sensors logs-sensors wait-for-kafka

# Default target
help:
	@echo "Factory Monitoring System - Available Commands:"
	@echo ""
	@echo "  setup         - Initialize environment and format Kafka storage"
	@echo "  start         - Start all services (infrastructure only)"
	@echo "  stop          - Stop all services"
	@echo "  restart       - Restart all services"
	@echo "  clean         - Clean up containers and volumes"
	@echo "  logs          - View aggregated logs"
	@echo "  status        - Check status of all services"
	@echo "  topics        - Create Kafka topics"
	@echo "  health        - Check health of all services"
	@echo "  test          - Run integration tests"
	@echo "  monitor       - Open Kafka UI in browser"
	@echo ""
	@echo "Sensor Management:"
	@echo "  build-sensors - Build sensor producer images"
	@echo "  start-sensors - Start sensor producers"
	@echo "  stop-sensors  - Stop sensor producers"
	@echo "  logs-sensors  - View sensor logs"
	@echo "  full-start    - Start infrastructure + sensors"
	@echo ""
	@echo "Consumer Management:"
	@echo "  build-consumers - Build consumer images"
	@echo "  start-consumers - Start consumer instances"
	@echo "  stop-consumers  - Stop consumer instances"
	@echo "  logs-consumers  - View consumer logs"
	@echo "  monitor-alerts  - Monitor alerts in real-time"
	@echo "  full-system     - Start complete system (infrastructure + sensors + consumers)"
	@echo ""

# Initialize environment and prepare Kafka storage
setup:
	@echo "Setting up Factory Monitoring System..."
	@echo "Creating necessary directories..."
	@mkdir -p logs
	@touch logs/.gitkeep
	@echo "Loading environment variables..."
	@if [ ! -f .env ]; then echo "Error: .env file not found!"; exit 1; fi
	@echo "Setup completed successfully!"

# Start infrastructure services only
start:
	@echo "Starting Factory Monitoring Infrastructure..."
	@docker compose up -d kafka1 kafka2 kafka3 postgres kafka-ui
	@echo "Waiting for Kafka brokers to start..."
	@$(MAKE) wait-for-kafka
	@echo "Creating Kafka topics..."
	@$(MAKE) topics
	@echo "Infrastructure started successfully!"
	@echo "Kafka UI available at: http://localhost:8080"
	@echo ""
	@echo "To start sensors, run: make start-sensors"

# Start all services including sensors
full-start:
	@echo "Starting complete Factory Monitoring System..."
	@docker compose up -d kafka1 kafka2 kafka3 postgres kafka-ui temperature-sensor vibration-sensor energy-sensor
	@echo "Waiting for Kafka brokers to start..."
	@$(MAKE) wait-for-kafka
	@echo "Creating Kafka topics..."
	@$(MAKE) topics
	@echo "Complete system started successfully!"
	@echo "Kafka UI available at: http://localhost:8080"

# Start complete system including consumers
full-system:
	@echo "Starting complete Factory Monitoring System with consumers..."
	@docker compose up -d
	@echo "Waiting for Kafka brokers to start..."
	@$(MAKE) wait-for-kafka
	@echo "Creating Kafka topics..."
	@$(MAKE) topics
	@echo "Complete system with consumers started successfully!"
	@echo "Kafka UI available at: http://localhost:8080"

# Stop all services
stop:
	@echo "Stopping Factory Monitoring System..."
	@docker compose down
	@echo "System stopped successfully!"

# Restart all services
restart: stop start

# Clean up containers and volumes
clean:
	@echo "Cleaning up Factory Monitoring System..."
	@echo "This will remove all containers, networks, and volumes!"
	@read -p "Are you sure? [y/N] " confirm && [ "$$confirm" = "y" ] || exit 1
	@docker compose down -v
	@docker system prune -f
	@echo "Cleanup completed!"

# View aggregated logs
logs:
	@echo "Viewing system logs (Ctrl+C to exit)..."
	@docker compose logs -f

# View logs for specific service
logs-%:
	@echo "Viewing logs for $*..."
	@docker compose logs -f $*

# Check status of all services
status:
	@echo "Factory Monitoring System Status:"
	@echo "=================================="
	@docker compose ps

# Create Kafka topics
topics:
	@echo "Creating Kafka topics..."
	@docker compose exec kafka1 kafka-topics \
		--bootstrap-server kafka1:29092 \
		--create \
		--topic sensor-data \
		--partitions 3 \
		--replication-factor 2 \
		--if-not-exists \
		--config cleanup.policy=delete \
		--config retention.ms=604800000
	@docker compose exec kafka1 kafka-topics \
		--bootstrap-server kafka1:29092 \
		--create \
		--topic alerts \
		--partitions 2 \
		--replication-factor 2 \
		--if-not-exists \
		--config cleanup.policy=delete \
		--config retention.ms=2592000000
	@echo "Topics created successfully!"
	@echo "Listing all topics:"
	@docker compose exec kafka1 kafka-topics --bootstrap-server kafka1:29092 --list

# Check health of all services
health:
	@echo "Checking service health..."
	@echo "=========================="
	@echo "Kafka Brokers:"
	@docker compose exec kafka1 kafka-broker-api-versions --bootstrap-server kafka1:29092 > /dev/null 2>&1 && echo "✓ Kafka1: Healthy" || echo "✗ Kafka1: Unhealthy"
	@docker compose exec kafka2 kafka-broker-api-versions --bootstrap-server kafka2:29092 > /dev/null 2>&1 && echo "✓ Kafka2: Healthy" || echo "✗ Kafka2: Unhealthy"
	@docker compose exec kafka3 kafka-broker-api-versions --bootstrap-server kafka3:29092 > /dev/null 2>&1 && echo "✓ Kafka3: Healthy" || echo "✗ Kafka3: Unhealthy"
	@echo ""
	@echo "PostgreSQL:"
	@docker compose exec postgres pg_isready -U factory_user > /dev/null 2>&1 && echo "✓ PostgreSQL: Healthy" || echo "✗ PostgreSQL: Unhealthy"

# Run integration tests (to be implemented later)
test:
	@echo "Running integration tests..."
	@echo "Tests will be implemented in Phase 8"

# Open Kafka UI in browser
monitor:
	@echo "Opening Kafka UI..."
	@echo "URL: http://localhost:8080"
	@python3 -c "import webbrowser; webbrowser.open('http://localhost:8080')" 2>/dev/null || \
		echo "Please open http://localhost:8080 in your browser"

# Development helpers
dev-reset: clean setup start

# Show cluster information
cluster-info:
	@echo "Kafka Cluster Information:"
	@echo "=========================="
	@docker compose exec kafka1 kafka-metadata-shell --snapshot /tmp/kraft-combined-logs/__cluster_metadata-0/00000000000000000000.log --print-brokers
	@echo ""
	@echo "Controller Status:"
	@docker compose exec kafka1 kafka-metadata-shell --snapshot /tmp/kraft-combined-logs/__cluster_metadata-0/00000000000000000000.log --print-controllers

# Tail logs from specific service
tail-%:
	@docker compose logs -f --tail=100 $*

# Comprehensive cluster verification
verify-cluster:
	@echo "Building cluster verification image..."
	@docker build -f docker/Dockerfile.tester -t factory-tester:latest .
	@echo "Running comprehensive cluster verification..."
	@docker run --rm --network t1_factory_network factory-tester:latest

# Quick cluster connectivity test
test-connectivity:
	@echo "Testing Kafka cluster connectivity..."
	@docker compose exec kafka1 kafka-broker-api-versions --bootstrap-server kafka1:29092 >/dev/null && echo "✓ Kafka1 accessible" || echo "✗ Kafka1 not accessible"
	@docker compose exec kafka2 kafka-broker-api-versions --bootstrap-server kafka2:29092 >/dev/null && echo "✓ Kafka2 accessible" || echo "✗ Kafka2 not accessible"
	@docker compose exec kafka3 kafka-broker-api-versions --bootstrap-server kafka3:29092 >/dev/null && echo "✓ Kafka3 accessible" || echo "✗ Kafka3 not accessible"

# Test external connectivity from host
test-external:
	@echo "Testing external Kafka connectivity from host..."
	@echo "================================================"
	@echo -n "Kafka1 (localhost:9092): "
	@timeout 5 nc -z localhost 9092 && echo "✓ Connected" || echo "✗ Connection failed"
	@echo -n "Kafka2 (localhost:9094): "
	@timeout 5 nc -z localhost 9094 && echo "✓ Connected" || echo "✗ Connection failed"
	@echo -n "Kafka3 (localhost:9096): "
	@timeout 5 nc -z localhost 9096 && echo "✓ Connected" || echo "✗ Connection failed"

# Test topic operations
test-topics:
	@echo "Testing topic operations..."
	@echo "Producing test message..."
	@echo '{"test": true, "timestamp": "'$$(date -u +%Y-%m-%dT%H:%M:%SZ)'", "sensor_id": "test-sensor"}' | docker compose exec -T kafka1 kafka-console-producer --bootstrap-server kafka1:29092 --topic sensor-data
	@echo "Consuming test message..."
	@timeout 10 docker compose exec kafka1 kafka-console-consumer --bootstrap-server kafka1:29092 --topic sensor-data --from-beginning --max-messages 1 || echo "Timeout reached - this is normal for testing"

# Build sensor producer images
build-sensors:
	@echo "Building sensor producer images..."
	@docker build -f docker/Dockerfile.producer -t sensor-producer:latest .
	@echo "Sensor images built successfully!"

# Build consumer images
build-consumers:
	@echo "Building consumer images..."
	@docker build -f docker/Dockerfile.consumer -t sensor-consumer:latest .
	@echo "Consumer images built successfully!"

# Build all images
build-all: build-sensors build-consumers

# Start sensor producers
start-sensors:
	@echo "Starting sensor producers..."
	@docker compose up -d temperature-sensor vibration-sensor energy-sensor
	@echo "Sensors started successfully!"

# Start consumer instances
start-consumers:
	@echo "Starting consumer instances..."
	@docker compose up -d consumer-1 consumer-2 consumer-3
	@echo "Consumers started successfully!"

# Stop sensor producers
stop-sensors:
	@echo "Stopping sensor producers..."
	@docker compose stop temperature-sensor vibration-sensor energy-sensor
	@echo "Sensors stopped!"

# Stop consumer instances
stop-consumers:
	@echo "Stopping consumer instances..."
	@docker compose stop consumer-1 consumer-2 consumer-3
	@echo "Consumers stopped!"

# View sensor logs
logs-sensors:
	@echo "Viewing sensor logs (Ctrl+C to exit)..."
	@docker compose logs -f temperature-sensor vibration-sensor energy-sensor

# View consumer logs
logs-consumers:
	@echo "Viewing consumer logs (Ctrl+C to exit)..."
	@docker compose logs -f consumer-1 consumer-2 consumer-3

# Monitor sensor data in real-time
monitor-sensors:
	@echo "Monitoring sensor data (Ctrl+C to exit)..."
	@docker compose exec kafka1 kafka-console-consumer \
		--bootstrap-server kafka1:29092 \
		--topic sensor-data \
		--from-beginning \
		--property print.timestamp=true \
		--property print.key=true

# Monitor alerts in real-time
monitor-alerts:
	@echo "Monitoring alerts (Ctrl+C to exit)..."
	@docker compose exec kafka1 kafka-console-consumer \
		--bootstrap-server kafka1:29092 \
		--topic alerts \
		--from-beginning \
		--property print.timestamp=true \
		--property print.key=true

# Wait for Kafka brokers to be ready
wait-for-kafka:
	@echo "Waiting for Kafka brokers to be ready..."
	@for i in $$(seq 1 60); do \
		if docker compose exec kafka1 kafka-broker-api-versions --bootstrap-server kafka1:29092 >/dev/null 2>&1 && \
		   docker compose exec kafka2 kafka-broker-api-versions --bootstrap-server kafka2:29092 >/dev/null 2>&1 && \
		   docker compose exec kafka3 kafka-broker-api-versions --bootstrap-server kafka3:29092 >/dev/null 2>&1; then \
			echo "✓ All Kafka brokers are ready!"; \
			$(MAKE) health; \
			break; \
		else \
			echo "⏳ Kafka brokers starting... ($$i/60)"; \
			sleep 2; \
		fi; \
		if [ $$i -eq 60 ]; then \
			echo "❌ Timeout waiting for Kafka brokers"; \
			$(MAKE) health; \
			exit 1; \
		fi; \
	done