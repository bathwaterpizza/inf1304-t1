# Makefile for Factory Monitoring System
# This file provides convenient commands for managing the distributed system

.PHONY: help setup all start stop clean status topics health test logs test-connectivity test-topics test-external
.PHONY: infrastructure-only with-consumers with-monitoring build-all build-producers build-consumers 
.PHONY: start-producers stop-producers start-consumers stop-consumers logs-producers logs-consumers
.PHONY: monitor-sensors monitor-alerts start-monitoring dashboard monitor wait-for-kafka

# Default target
help:
	@echo "Factory Monitoring System - Available Commands:"
	@echo ""
	@echo "Quick Start:"
	@echo "  all           - Build and start complete system (infrastructure + producers + consumers + monitoring)"
	@echo "  setup         - Initialize environment and format Kafka storage"
	@echo "  start         - Start infrastructure services only (Kafka + PostgreSQL + Kafka UI)"
	@echo "  stop          - Stop all services"
	@echo "  restart       - Restart all services"
	@echo "  clean         - Clean up containers and volumes"
	@echo "  status        - Check status of all services"
	@echo "  health        - Check health of all services"
	@echo "  logs          - View aggregated logs"
	@echo ""
	@echo "Component Management:"
	@echo "  build-all     - Build all Docker images"
	@echo "  build-producers - Build sensor producer images"
	@echo "  build-consumers - Build consumer images"
	@echo "  start-producers - Start sensor producers"
	@echo "  stop-producers  - Stop sensor producers"
	@echo "  start-consumers - Start consumer instances"
	@echo "  stop-consumers  - Stop consumer instances"
	@echo "  start-monitoring - Start monitoring dashboard"
	@echo ""
	@echo "System Startup Options:"
	@echo "  infrastructure-only  - Start infrastructure + producers (no consumers, no monitoring)"
	@echo "  with-consumers      - Start infrastructure + producers + consumers (no monitoring)"
	@echo "  with-monitoring     - Start complete system with monitoring dashboard"
	@echo ""
	@echo "Monitoring & Debugging:"
	@echo "  dashboard     - Open monitoring dashboard in browser"
	@echo "  monitor       - Open Kafka UI in browser"
	@echo "  logs-producers - View sensor producer logs"
	@echo "  logs-consumers - View consumer logs"
	@echo "  monitor-sensors  - Monitor sensor data stream in real-time"
	@echo "  monitor-alerts   - Monitor alerts in real-time"
	@echo ""
	@echo "Testing & Verification:"
	@echo "  topics        - Create Kafka topics"
	@echo "  test-external - Test external connectivity"
	@echo "  test-topics   - Test topic operations"
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

# Build and start complete system (infrastructure + producers + consumers + monitoring)
all: build-all
	@echo "Building and starting complete Factory Monitoring System..."
	@docker compose up -d
	@echo "Waiting for Kafka brokers to start..."
	@$(MAKE) wait-for-kafka
	@echo "Creating Kafka topics..."
	@$(MAKE) topics
	@echo "Complete system started successfully!"
	@echo "Kafka UI available at: http://localhost:8080"
	@echo "Monitoring Dashboard available at: http://localhost:5000"
	@echo ""
	@echo "🎉 System is ready! Use 'make dashboard' to open monitoring dashboard"

# Start infrastructure services only (Kafka + PostgreSQL + Kafka UI)
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
	@echo "To start producers, run: make start-producers"
	@echo "To start consumers, run: make start-consumers"

# Start infrastructure + producers (no consumers, no monitoring)
infrastructure-only:
	@echo "Starting infrastructure with sensor producers..."
	@docker compose up -d kafka1 kafka2 kafka3 postgres kafka-ui temperature-sensor vibration-sensor energy-sensor
	@echo "Waiting for Kafka brokers to start..."
	@$(MAKE) wait-for-kafka
	@echo "Creating Kafka topics..."
	@$(MAKE) topics
	@echo "Infrastructure with producers started successfully!"
	@echo "Kafka UI available at: http://localhost:8080"

# Start infrastructure + producers + consumers (no monitoring)
with-consumers:
	@echo "Starting complete system with consumers (no monitoring)..."
	@docker compose up -d kafka1 kafka2 kafka3 postgres kafka-ui temperature-sensor vibration-sensor energy-sensor consumer-1 consumer-2 consumer-3
	@echo "Waiting for Kafka brokers to start..."
	@$(MAKE) wait-for-kafka
	@echo "Creating Kafka topics..."
	@$(MAKE) topics
	@echo "System with consumers started successfully!"
	@echo "Kafka UI available at: http://localhost:8080"

# Start complete system with monitoring dashboard
with-monitoring:
	@echo "Starting complete system with monitoring dashboard..."
	@docker compose up -d
	@echo "Waiting for Kafka brokers to start..."
	@$(MAKE) wait-for-kafka
	@echo "Creating Kafka topics..."
	@$(MAKE) topics
	@echo "Complete system with monitoring started successfully!"
	@echo "Kafka UI available at: http://localhost:8080"
	@echo "Monitoring Dashboard available at: http://localhost:5000"

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
	-@docker compose down -v
	-@docker system prune -f
	-@docker stop $$(docker ps -aq)
	-@docker rm $$(docker ps -aq)
	-@docker rmi $$(docker images -q)
	-@docker volume rm $$(docker volume ls -q)
	-@docker builder prune
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
		--replication-factor 3 \
		--if-not-exists \
		--config cleanup.policy=delete \
		--config retention.ms=604800000
	@docker compose exec kafka1 kafka-topics \
		--bootstrap-server kafka1:29092 \
		--create \
		--topic alerts \
		--partitions 2 \
		--replication-factor 3 \
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
build-producers:
	@echo "Building sensor producer images..."
	@docker build -f docker/Dockerfile.producer -t sensor-producer:latest .
	@echo "Producer images built successfully!"

# Build consumer images
build-consumers:
	@echo "Building consumer images..."
	@docker build -f docker/Dockerfile.consumer -t sensor-consumer:latest .
	@echo "Consumer images built successfully!"

# Build all images (producers + consumers + monitoring)
build-all: build-producers build-consumers
	@echo "Building monitoring service image..."
	@docker build -f docker/Dockerfile.monitoring -t monitoring-service:latest .
	@echo "All images built successfully!"

# Start sensor producers
start-producers:
	@echo "Starting sensor producers..."
	@docker compose up -d temperature-sensor vibration-sensor energy-sensor
	@echo "Producers started successfully!"

# Start consumer instances
start-consumers:
	@echo "Starting consumer instances..."
	@docker compose up -d consumer-1 consumer-2 consumer-3
	@echo "Consumers started successfully!"

# Stop sensor producers
stop-producers:
	@echo "Stopping sensor producers..."
	@docker compose stop temperature-sensor vibration-sensor energy-sensor
	@echo "Producers stopped!"

# Stop consumer instances
stop-consumers:
	@echo "Stopping consumer instances..."
	@docker compose stop consumer-1 consumer-2 consumer-3
	@echo "Consumers stopped!"

# View sensor producer logs
logs-producers:
	@echo "Viewing producer logs (Ctrl+C to exit)..."
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

# Start monitoring service only
start-monitoring:
	@echo "Starting monitoring dashboard..."
	@docker compose up -d monitoring
	@echo "Monitoring dashboard started successfully!"
	@echo "Dashboard available at: http://localhost:5000"

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