# Makefile for Factory Monitoring System
# This file provides convenient commands for managing the distributed system

.PHONY: help setup start stop clean status topics health test logs verify-cluster test-connectivity test-topics test-external
	@docker compose exec kafka2 kafka-broker-api-versions --bootstrap-server localhost:9094 > /dev/null 2>&1 && echo "✓ Kafka2: Healthy" || echo "✗ Kafka2: Unhealthy"
	@docker compose exec kafka3 kafka-broker-api-versions --bootstrap-server localhost:9096 > /dev/null 2>&1 && echo "✓ Kafka3: Healthy" || echo "✗ Kafka3: Unhealthy"
	@echo ""
	@echo "PostgreSQL:"
	@docker compose exec postgres pg_isready -U factory_user > /dev/null 2>&1 && echo "✓ PostgreSQL: Healthy" || echo "✗ PostgreSQL: Unhealthy"tem

.PHONY: help setup start stop clean logs test status topics health

# Default target
help:
	@echo "Factory Monitoring System - Available Commands:"
	@echo ""
	@echo "  setup     - Initialize environment and format Kafka storage"
	@echo "  start     - Start all services"
	@echo "  stop      - Stop all services"
	@echo "  restart   - Restart all services"
	@echo "  clean     - Clean up containers and volumes"
	@echo "  logs      - View aggregated logs"
	@echo "  status    - Check status of all services"
	@echo "  topics    - Create Kafka topics"
	@echo "  health    - Check health of all services"
	@echo "  test      - Run integration tests"
	@echo "  monitor   - Open Kafka UI in browser"
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

# Start all services
start:
	@echo "Starting Factory Monitoring System..."
	@docker compose up -d
	@echo "Waiting for services to be ready..."
	@sleep 10
	@$(MAKE) health
	@echo "Creating Kafka topics..."
	@$(MAKE) topics
	@echo "System started successfully!"
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