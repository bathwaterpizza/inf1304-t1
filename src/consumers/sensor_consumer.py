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
from confluent_kafka import Consumer, Producer, KafkaError


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
    ):
        """
        Initialize the sensor consumer.

        Args:
            consumer_id: Unique identifier for this consumer instance
            kafka_brokers: Kafka bootstrap servers
            sensor_topic: Topic to consume sensor data from
            alert_topic: Topic to publish alerts to
            consumer_group: Consumer group for load balancing
        """
        self.consumer_id = consumer_id
        self.sensor_topic = sensor_topic
        self.alert_topic = alert_topic
        self.consumer_group = consumer_group
        self.running = False
        self.processed_count = 0

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
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

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        # Anomaly detection thresholds and patterns
        self.anomaly_patterns = self._load_anomaly_patterns()
        self.recent_readings = {}  # Store recent readings for pattern analysis

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.stop()

    def _load_anomaly_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load anomaly detection patterns for different sensor types."""
        return {
            "temperature": {
                "consecutive_high_threshold": 3,  # Number of consecutive high readings
                "rapid_change_threshold": 10.0,  # °C change per reading
                "baseline_deviation": 15.0,  # °C deviation from baseline
                "time_window_minutes": 5,
            },
            "vibration": {
                "consecutive_high_threshold": 2,
                "rapid_change_threshold": 3.0,  # mm/s change per reading
                "baseline_deviation": 2.0,  # mm/s deviation from baseline
                "time_window_minutes": 3,
            },
            "energy": {
                "consecutive_high_threshold": 3,
                "rapid_change_threshold": 50.0,  # kW change per reading
                "baseline_deviation": 40.0,  # kW deviation from baseline
                "time_window_minutes": 10,
            },
            "humidity": {
                "consecutive_high_threshold": 4,
                "rapid_change_threshold": 15.0,  # % change per reading
                "baseline_deviation": 20.0,  # % deviation from baseline
                "time_window_minutes": 8,
            },
            "pressure": {
                "consecutive_high_threshold": 3,
                "rapid_change_threshold": 20.0,  # hPa change per reading
                "baseline_deviation": 30.0,  # hPa deviation from baseline
                "time_window_minutes": 5,
            },
        }

    def process_sensor_data(
        self, sensor_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Process sensor data and detect anomalies.

        Args:
            sensor_data: Parsed sensor reading

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

        # Detect anomalies based on patterns
        anomaly_type = self._detect_anomaly(sensor_id, sensor_type, sensor_data)

        if anomaly_type:
            alert = self._create_alert(sensor_data, anomaly_type)
            self.logger.warning(
                f"Anomaly detected for {sensor_id}: {anomaly_type} - "
                f"Value: {value}{sensor_data.get('unit', '')} (Alert: {current_alert_level})"
            )
            return alert

        # Log normal processing
        self.logger.info(
            f"Processed {sensor_type} reading from {sensor_id}: "
            f"{value}{sensor_data.get('unit', '')} (Alert: {current_alert_level})"
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

        try:
            while self.running:
                # Poll for messages
                msg = self.consumer.poll(timeout=1.0)

                if msg is None:
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

                    # Process sensor data and detect anomalies
                    alert = self.process_sensor_data(sensor_data)

                    # Publish alert if anomaly detected
                    if alert:
                        self.publish_alert(alert)

                    self.processed_count += 1

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
