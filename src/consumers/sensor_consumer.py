"""
Unified Sensor Data Consumer

A unified consumer that processes all types of sensor data from Kafka,
performs anomaly detection, generates alerts, and stores processed data.
"""

import asyncio
import json
import logging
import os
import signal
import time
from datetime import datetime
from typing import Dict, Any, Optional
from confluent_kafka import Consumer, Producer, KafkaError  # type: ignore
import psycopg2  # type: ignore  # noqa: F401
from psycopg2.extras import RealDictCursor  # type: ignore  # noqa: F401
from psycopg2.pool import SimpleConnectionPool  # type: ignore


class SensorConsumer:
    """
    Unified sensor data consumer that processes all sensor types
    and performs real-time anomaly detection and alert generation.
    """

    def __init__(
        self,
        consumer_id: str,
        kafka_brokers: str,
        sensor_topic: str = "sensor-data",
        alert_topic: str = "alerts",
        consumer_group: str = "sensor-processors",
        database_url: Optional[str] = None,
    ):
        """
        Initialize the sensor consumer.

        Args:
            consumer_id: Unique identifier for this consumer instance
            kafka_brokers: Kafka bootstrap servers
            sensor_topic: Topic to consume sensor data from
            alert_topic: Topic to publish alerts to
            consumer_group: Consumer group for load balancing
            database_url: PostgreSQL connection URL
        """
        self.consumer_id = consumer_id
        self.sensor_topic = sensor_topic
        self.alert_topic = alert_topic
        self.consumer_group = consumer_group
        self.database_url = database_url or os.getenv("DATABASE_URL")
        self.running = False
        self.processed_count = 0
        self.last_heartbeat = time.time()
        self.assigned_partitions = []

        # Setup logging
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        logging.basicConfig(
            level=getattr(logging, log_level, logging.INFO),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        self.logger = logging.getLogger(f"consumer-{consumer_id}")

        # Setup Kafka consumer
        consumer_config = {
            "bootstrap.servers": kafka_brokers,
            "group.id": consumer_group,
            "client.id": f"consumer-{consumer_id}",
            "auto.offset.reset": "earliest",
            "enable.auto.commit": True,
            "auto.commit.interval.ms": 5000,
            "session.timeout.ms": 30000,
            "heartbeat.interval.ms": 10000,
        }

        # Setup Kafka producer for alerts
        producer_config = {
            "bootstrap.servers": kafka_brokers,
            "client.id": f"alert-producer-{consumer_id}",
            "acks": "all",
            "retries": 3,
            "compression.type": "snappy",
        }

        try:
            self.consumer = Consumer(consumer_config)
            self.producer = Producer(producer_config)
            self.logger.info(
                f"Kafka consumer/producer initialized for consumer {consumer_id}"
            )
        except Exception as e:
            self.logger.error(f"Failed to initialize Kafka client: {e}")
            raise

        # Subscribe to sensor data topic
        self.consumer.subscribe([sensor_topic])
        self.logger.info(f"Subscribed to topic: {sensor_topic}")

        # Setup rebalance callbacks to track partition assignments
        self.consumer.subscribe(
            [sensor_topic], on_assign=self._on_assign, on_revoke=self._on_revoke
        )

        # Setup database connection
        self.db_pool = None
        if self.database_url:
            self._init_database()

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        # Anomaly detection thresholds and patterns
        self.anomaly_patterns = self._load_anomaly_patterns()
        self.recent_readings = {}  # Store recent readings for pattern analysis

    def _on_assign(self, consumer, partitions):
        """Callback when partitions are assigned to this consumer."""
        self.assigned_partitions = [p.partition for p in partitions]
        self.logger.info(f"Partitions assigned: {self.assigned_partitions}")

        # Record rebalancing event
        self._record_rebalancing_event("partition_assigned", partitions)

        # Update consumer health status
        self._update_consumer_health()

    def _on_revoke(self, consumer, partitions):
        """Callback when partitions are revoked from this consumer."""
        revoked_partitions = [p.partition for p in partitions]
        self.logger.info(f"Partitions revoked: {revoked_partitions}")

        # Record rebalancing event
        self._record_rebalancing_event("partition_revoked", partitions)

    def _record_rebalancing_event(self, event_type: str, partitions):
        """Record rebalancing events in the database."""
        if not self.db_pool:
            return

        conn = None
        try:
            conn = self.db_pool.getconn()
            cursor = conn.cursor()

            for partition in partitions:
                insert_query = """
                    INSERT INTO rebalancing_events (
                        event_type, consumer_id, partition_number, topic_name, timestamp_utc
                    ) VALUES (%s, %s, %s, %s, %s)
                """
                cursor.execute(
                    insert_query,
                    (
                        event_type,
                        self.consumer_id,
                        partition.partition,
                        partition.topic,
                        datetime.utcnow(),
                    ),
                )

            conn.commit()
            self.logger.info(
                f"Recorded {event_type} event for {len(partitions)} partitions"
            )

        except Exception as e:
            self.logger.error(f"Error recording rebalancing event: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                self.db_pool.putconn(conn)

    def _update_consumer_health(self):
        """Update consumer health status in database."""
        if not self.db_pool:
            return

        conn = None
        try:
            conn = self.db_pool.getconn()
            cursor = conn.cursor()

            # Calculate messages processed in last minute
            messages_last_minute = self._get_messages_processed_last_minute()

            # Update or insert consumer health record
            upsert_query = """
                INSERT INTO consumer_health (
                    consumer_id, status, assigned_partitions, last_heartbeat, 
                    messages_processed_last_minute, total_messages_processed
                ) VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (consumer_id) DO UPDATE SET
                    status = EXCLUDED.status,
                    assigned_partitions = EXCLUDED.assigned_partitions,
                    last_heartbeat = EXCLUDED.last_heartbeat,
                    messages_processed_last_minute = EXCLUDED.messages_processed_last_minute,
                    total_messages_processed = EXCLUDED.total_messages_processed,
                    updated_at = CURRENT_TIMESTAMP
            """

            cursor.execute(
                upsert_query,
                (
                    self.consumer_id,
                    "active",
                    json.dumps(self.assigned_partitions),
                    datetime.utcnow(),
                    messages_last_minute,
                    self.processed_count,
                ),
            )

            conn.commit()

        except Exception as e:
            self.logger.error(f"Error updating consumer health: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                self.db_pool.putconn(conn)

    def _get_messages_processed_last_minute(self) -> int:
        """Get count of messages processed in the last minute."""
        if not self.db_pool:
            return 0

        conn = None
        try:
            conn = self.db_pool.getconn()
            cursor = conn.cursor()

            query = """
                SELECT COUNT(*) FROM sensor_readings 
                WHERE processed_by_consumer = %s 
                AND processing_timestamp >= NOW() - INTERVAL '1 minute'
            """
            cursor.execute(query, (self.consumer_id,))
            result = cursor.fetchone()
            return result[0] if result else 0

        except Exception as e:
            self.logger.error(f"Error getting messages processed: {e}")
            return 0
        finally:
            if conn:
                self.db_pool.putconn(conn)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.stop()

    def _init_database(self):
        """Initialize PostgreSQL connection pool."""
        try:
            # Create connection pool
            self.db_pool = SimpleConnectionPool(
                minconn=1, maxconn=5, dsn=self.database_url
            )

            # Test connection and register sensors
            self._register_sensors()
            self.logger.info("Database connection pool initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            self.db_pool = None

    def _register_sensors(self):
        """Register sensors in the database if they don't exist."""
        if not self.db_pool:
            return

        conn = None
        try:
            conn = self.db_pool.getconn()

            # This will be called by each consumer, but INSERT ON CONFLICT will handle duplicates
            # We'll register sensors as we encounter them in the data
            self.logger.debug("Sensor registration ready")

        except Exception as e:
            self.logger.error(f"Error setting up sensor registration: {e}")
        finally:
            if conn:
                self.db_pool.putconn(conn)

    def _load_anomaly_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load anomaly detection patterns for different sensor types with environment overrides."""
        return {
            "temperature": {
                "consecutive_high_threshold": 3,  # Number of consecutive high readings
                "rapid_change_threshold": 10.0,  # °C change per reading
                "baseline_deviation": 15.0,  # °C deviation from baseline
                "time_window_minutes": 5,
                "warning_threshold": float(
                    os.getenv("TEMPERATURE_WARNING_THRESHOLD", "35.0")
                ),
                "critical_threshold": float(
                    os.getenv("TEMPERATURE_CRITICAL_THRESHOLD", "40.0")
                ),
            },
            "vibration": {
                "consecutive_high_threshold": 2,
                "rapid_change_threshold": 3.0,  # mm/s change per reading
                "baseline_deviation": 2.0,  # mm/s deviation from baseline
                "time_window_minutes": 3,
                "warning_threshold": float(
                    os.getenv("VIBRATION_WARNING_THRESHOLD", "5.0")
                ),
                "critical_threshold": float(
                    os.getenv("VIBRATION_CRITICAL_THRESHOLD", "7.0")
                ),
            },
            "energy": {
                "consecutive_high_threshold": 3,
                "rapid_change_threshold": 50.0,  # kW change per reading
                "baseline_deviation": 40.0,  # kW deviation from baseline
                "time_window_minutes": 10,
                "anomaly_threshold": float(
                    os.getenv("ENERGY_ANOMALY_THRESHOLD", "20.0")
                ),
                "warning_threshold": 150.0,
                "critical_threshold": 180.0,
            },
            "humidity": {
                "consecutive_high_threshold": 4,
                "rapid_change_threshold": 15.0,  # % change per reading
                "baseline_deviation": 20.0,  # % deviation from baseline
                "time_window_minutes": 8,
                "warning_threshold": 60.0,
                "critical_threshold": 65.0,
            },
            "pressure": {
                "consecutive_high_threshold": 3,
                "rapid_change_threshold": 20.0,  # hPa change per reading
                "baseline_deviation": 30.0,  # hPa deviation from baseline
                "time_window_minutes": 5,
                "warning_threshold": 1040.0,
                "critical_threshold": 1045.0,
            },
        }

    def _store_sensor_reading(
        self, sensor_data: Dict[str, Any], kafka_msg=None
    ) -> bool:
        """Store sensor reading in the database with processing metadata."""
        if not self.db_pool:
            return False

        conn = None
        try:
            conn = self.db_pool.getconn()
            cursor = conn.cursor()

            # Ensure sensor exists
            self._ensure_sensor_exists(cursor, sensor_data)

            # Insert sensor reading with processing metadata
            insert_query = """
                INSERT INTO sensor_readings (
                    sensor_id, timestamp_utc, sensor_type, reading_value, 
                    unit, alert_level, quality, location, metadata,
                    processed_by_consumer, kafka_partition, kafka_offset, processing_timestamp
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            # Extract Kafka metadata if available
            partition = kafka_msg.partition() if kafka_msg else None
            offset = kafka_msg.offset() if kafka_msg else None

            cursor.execute(
                insert_query,
                (
                    sensor_data.get("sensor_id"),
                    sensor_data.get("timestamp"),
                    sensor_data.get("sensor_type"),
                    sensor_data.get("value"),
                    sensor_data.get("unit"),
                    sensor_data.get("alert_level", "normal"),
                    sensor_data.get("quality", 1.0),
                    json.dumps(sensor_data.get("location", {})),
                    json.dumps(sensor_data.get("metadata", {})),
                    self.consumer_id,  # processed_by_consumer
                    partition,  # kafka_partition
                    offset,  # kafka_offset
                    datetime.utcnow(),  # processing_timestamp
                ),
            )

            conn.commit()
            return True

        except Exception as e:
            self.logger.error(f"Error storing sensor reading: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                self.db_pool.putconn(conn)

    def _store_alert(self, alert_data: Dict[str, Any]) -> bool:
        """Store alert in the database."""
        if not self.db_pool:
            return False

        conn = None
        try:
            conn = self.db_pool.getconn()
            cursor = conn.cursor()

            insert_query = """
                INSERT INTO alerts (
                    alert_id, sensor_id, sensor_type, anomaly_type, severity,
                    sensor_value, sensor_unit, sensor_alert_level, description,
                    location, detected_by, timestamp_utc, metadata
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (alert_id) DO NOTHING
            """

            cursor.execute(
                insert_query,
                (
                    alert_data.get("alert_id"),
                    alert_data.get("sensor_id"),
                    alert_data.get("sensor_type"),
                    alert_data.get("anomaly_type"),
                    alert_data.get("severity"),
                    alert_data.get("sensor_value"),
                    alert_data.get("sensor_unit"),
                    alert_data.get("sensor_alert_level"),
                    alert_data.get("description"),
                    json.dumps(alert_data.get("location", {})),
                    alert_data.get("detected_by"),
                    alert_data.get("timestamp"),
                    json.dumps({}),  # Additional metadata
                ),
            )

            conn.commit()
            return True

        except Exception as e:
            self.logger.error(f"Error storing alert: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                self.db_pool.putconn(conn)

    def _ensure_sensor_exists(self, cursor, sensor_data: Dict[str, Any]):
        """Ensure sensor exists in the database."""
        try:
            insert_query = """
                INSERT INTO sensors (sensor_id, sensor_type, location, metadata)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (sensor_id) DO NOTHING
            """

            # Extract metadata from sensor_data
            metadata = sensor_data.get("metadata", {})

            cursor.execute(
                insert_query,
                (
                    sensor_data.get("sensor_id"),
                    sensor_data.get("sensor_type"),
                    json.dumps(sensor_data.get("location", {})),
                    json.dumps(metadata),
                ),
            )

        except Exception as e:
            self.logger.error(f"Error ensuring sensor exists: {e}")

    def process_sensor_data(
        self, sensor_data: Dict[str, Any], kafka_msg=None
    ) -> Optional[Dict[str, Any]]:
        """
        Process sensor data and detect anomalies.

        Args:
            sensor_data: Parsed sensor reading
            kafka_msg: Kafka message object for metadata

        Returns:
            Alert data if anomaly detected, None otherwise
        """
        sensor_id = sensor_data.get("sensor_id")
        sensor_type = sensor_data.get("sensor_type")
        value = sensor_data.get("value")
        timestamp = sensor_data.get("timestamp")
        current_alert_level = sensor_data.get("alert_level", "normal")

        # Store recent reading for pattern analysis
        if sensor_id not in self.recent_readings:
            self.recent_readings[sensor_id] = []

        self.recent_readings[sensor_id].append(
            {"timestamp": timestamp, "value": value, "alert_level": current_alert_level}
        )

        # Keep only recent readings (last 10 readings)
        self.recent_readings[sensor_id] = self.recent_readings[sensor_id][-10:]

        # Store sensor reading in database with processing metadata
        self._store_sensor_reading(sensor_data, kafka_msg)

        # Detect anomalies based on patterns
        anomaly_type = self._detect_anomaly(sensor_id, sensor_type, sensor_data)

        if anomaly_type:
            alert = self._create_alert(sensor_data, anomaly_type)
            # Store alert in database
            self._store_alert(alert)
            self.logger.warning(
                f"Anomaly detected for {sensor_id}: {anomaly_type} - "
                f"Value: {value}{sensor_data.get('unit', '')} (Alert: {current_alert_level})"
            )
            return alert

        # Log normal processing
        partition_info = f" [partition {kafka_msg.partition()}]" if kafka_msg else ""
        self.logger.info(
            f"Processed {sensor_type} reading from {sensor_id}: "
            f"{value}{sensor_data.get('unit', '')} (Alert: {current_alert_level}){partition_info}"
        )
        return None

    def _detect_anomaly(
        self, sensor_id: str, sensor_type: str, current_data: Dict[str, Any]
    ) -> Optional[str]:
        """
        Detect anomalies based on sensor patterns and thresholds.

        Args:
            sensor_id: Sensor identifier
            sensor_type: Type of sensor
            current_data: Current sensor reading

        Returns:
            Anomaly type if detected, None otherwise
        """
        if sensor_type not in self.anomaly_patterns:
            return None

        pattern = self.anomaly_patterns[sensor_type]
        readings = self.recent_readings.get(sensor_id, [])

        if len(readings) < 2:
            return None

        current_value = current_data.get("value")
        current_alert = current_data.get("alert_level", "normal")

        # 1. Check for consecutive critical/warning alerts
        if len(readings) >= pattern["consecutive_high_threshold"]:
            recent_alerts = [
                r["alert_level"]
                for r in readings[-pattern["consecutive_high_threshold"] :]
            ]
            if all(alert in ["warning", "critical"] for alert in recent_alerts):
                return "consecutive_high_alerts"

        # 2. Check for rapid value changes
        if len(readings) >= 2:
            prev_value = readings[-2]["value"]
            change = abs(current_value - prev_value)
            if change > pattern["rapid_change_threshold"]:
                return "rapid_value_change"

        # 3. Check for baseline deviation
        if len(readings) >= 5:
            recent_values = [r["value"] for r in readings[-5:]]
            baseline = sum(recent_values[:-1]) / len(recent_values[:-1])
            deviation = abs(current_value - baseline)
            if deviation > pattern["baseline_deviation"]:
                return "baseline_deviation"

        # 4. Check for immediate critical alerts
        if current_alert == "critical":
            return "critical_threshold_violation"

        return None

    def _create_alert(
        self, sensor_data: Dict[str, Any], anomaly_type: str
    ) -> Dict[str, Any]:
        """
        Create alert message for detected anomaly.

        Args:
            sensor_data: Original sensor data
            anomaly_type: Type of anomaly detected

        Returns:
            Alert message dictionary
        """
        alert_severity = self._determine_alert_severity(
            anomaly_type, sensor_data.get("alert_level")
        )

        alert = {
            "alert_id": f"alert-{int(time.time() * 1000)}-{self.consumer_id}",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "sensor_id": sensor_data.get("sensor_id"),
            "sensor_type": sensor_data.get("sensor_type"),
            "anomaly_type": anomaly_type,
            "severity": alert_severity,
            "sensor_value": sensor_data.get("value"),
            "sensor_unit": sensor_data.get("unit"),
            "sensor_alert_level": sensor_data.get("alert_level"),
            "location": sensor_data.get("location"),
            "detected_by": self.consumer_id,
            "description": self._get_anomaly_description(anomaly_type, sensor_data),
        }

        return alert

    def _determine_alert_severity(
        self, anomaly_type: str, sensor_alert_level: str
    ) -> str:
        """Determine overall alert severity based on anomaly type and sensor alert level."""
        if (
            sensor_alert_level == "critical"
            or anomaly_type == "critical_threshold_violation"
        ):
            return "high"
        elif anomaly_type in ["consecutive_high_alerts", "rapid_value_change"]:
            return "medium"
        else:
            return "low"

    def _get_anomaly_description(
        self, anomaly_type: str, sensor_data: Dict[str, Any]
    ) -> str:
        """Generate human-readable description for anomaly."""
        sensor_type = sensor_data.get("sensor_type", "unknown")
        value = sensor_data.get("value")
        unit = sensor_data.get("unit", "")

        descriptions = {
            "consecutive_high_alerts": f"Multiple consecutive high {sensor_type} readings detected",
            "rapid_value_change": f"Rapid {sensor_type} change detected: {value}{unit}",
            "baseline_deviation": f"{sensor_type.title()} value {value}{unit} deviates significantly from baseline",
            "critical_threshold_violation": f"Critical {sensor_type} threshold violated: {value}{unit}",
        }

        return descriptions.get(
            anomaly_type, f"Anomaly detected in {sensor_type} sensor"
        )

    def publish_alert(self, alert: Dict[str, Any]) -> bool:
        """
        Publish alert to Kafka alerts topic.

        Args:
            alert: Alert message to publish

        Returns:
            True if successful, False otherwise
        """
        try:
            message_key = alert["sensor_id"]
            message_value = json.dumps(alert)

            self.producer.produce(
                topic=self.alert_topic,
                key=message_key,
                value=message_value,
                callback=self._alert_delivery_callback,
            )

            # Poll for delivery reports
            self.producer.poll(0)
            return True

        except Exception as e:
            self.logger.error(f"Failed to publish alert: {e}")
            return False

    def _alert_delivery_callback(self, err, msg):
        """Callback for alert message delivery reports."""
        if err is not None:
            self.logger.error(f"Alert delivery failed: {err}")
        else:
            self.logger.info(f"Alert delivered to {msg.topic()} [{msg.partition()}]")

    async def run(self):
        """Main consumer loop."""
        self.running = True
        self.logger.info(
            f"Starting sensor consumer {self.consumer_id} "
            f"(group: {self.consumer_group}, topic: {self.sensor_topic})"
        )

        # Initial health update
        self._update_consumer_health()

        try:
            while self.running:
                # Poll for messages
                msg = self.consumer.poll(timeout=1.0)

                if msg is None:
                    # Update heartbeat periodically even when no messages
                    current_time = time.time()
                    if (
                        current_time - self.last_heartbeat > 2
                    ):  # Update every 2 seconds for real-time monitoring
                        self._update_consumer_health()
                        self.last_heartbeat = current_time
                    continue

                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        # End of partition event
                        self.logger.debug(f"Reached end of partition {msg.partition()}")
                    else:
                        self.logger.error(f"Consumer error: {msg.error()}")
                    continue

                try:
                    # Parse sensor data
                    sensor_data = json.loads(msg.value().decode("utf-8"))

                    # Process sensor data and detect anomalies (pass Kafka message for metadata)
                    alert = self.process_sensor_data(sensor_data, msg)

                    # Publish alert if anomaly detected
                    if alert:
                        self.publish_alert(alert)

                    self.processed_count += 1

                    # Update health status periodically
                    current_time = time.time()
                    if (
                        current_time - self.last_heartbeat > 2
                    ):  # Update every 2 seconds for real-time monitoring
                        self._update_consumer_health()
                        self.last_heartbeat = current_time

                    # Log processing stats periodically
                    if self.processed_count % 100 == 0:
                        self.logger.info(f"Processed {self.processed_count} messages")

                except json.JSONDecodeError as e:
                    self.logger.error(f"Failed to parse message: {e}")
                except Exception as e:
                    self.logger.error(f"Error processing message: {e}")

                # Small delay to prevent overwhelming the system
                await asyncio.sleep(0.1)

        except Exception as e:
            self.logger.error(f"Error in consumer loop: {e}")
        finally:
            self.cleanup()

    def stop(self):
        """Stop the consumer."""
        self.logger.info("Stopping consumer...")
        self.running = False

    def cleanup(self):
        """Clean up resources."""
        try:
            if self.consumer:
                self.logger.info("Closing consumer...")
                self.consumer.close()

            if self.producer:
                self.logger.info("Flushing remaining alert messages...")
                remaining = self.producer.flush(timeout=10)
                if remaining > 0:
                    self.logger.warning(f"{remaining} alert messages not delivered")

            if self.db_pool:
                self.logger.info("Closing database connection pool...")
                self.db_pool.closeall()

            self.logger.info(
                f"Consumer {self.consumer_id} stopped. Total processed: {self.processed_count}"
            )

        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")


async def main():
    """Main function."""
    # Get configuration from environment
    consumer_id = os.getenv("CONSUMER_ID", f"consumer-{int(time.time())}")
    kafka_brokers = os.getenv("KAFKA_BROKERS", "kafka1:29092,kafka2:29092,kafka3:29092")
    sensor_topic = os.getenv("SENSOR_TOPIC", "sensor-data")
    alert_topic = os.getenv("ALERT_TOPIC", "alerts")
    consumer_group = os.getenv("CONSUMER_GROUP", "sensor-processors")

    # Create and run consumer
    consumer = SensorConsumer(
        consumer_id=consumer_id,
        kafka_brokers=kafka_brokers,
        sensor_topic=sensor_topic,
        alert_topic=alert_topic,
        consumer_group=consumer_group,
    )

    try:
        await consumer.run()
    except KeyboardInterrupt:
        consumer.logger.info("Consumer stopped by user")
    finally:
        consumer.stop()


if __name__ == "__main__":
    asyncio.run(main())
