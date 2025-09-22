"""
Simple Sensor Producer

A unified sensor simulator that can generate various types of sensor data
(temperature, vibration, energy) and publish to Kafka.
"""

import asyncio
import json
import logging
import os
import random
import signal
import time
from datetime import datetime
from typing import Dict, Any
from confluent_kafka import Producer  # type: ignore


class SensorProducer:
    """
    Simple sensor data producer that generates randomized sensor readings
    and publishes them to Kafka.
    """

    def __init__(
        self,
        sensor_id: str,
        sensor_type: str,
        kafka_brokers: str,
        topic: str = "sensor-data",
        interval: float = 5.0,
    ):
        """
        Initialize the sensor producer.

        Args:
            sensor_id: Unique identifier for this sensor
            sensor_type: Type of sensor (temperature, vibration, energy)
            kafka_brokers: Kafka bootstrap servers
            topic: Kafka topic to publish to
            interval: Interval between readings in seconds
        """
        self.sensor_id = sensor_id
        self.sensor_type = sensor_type
        self.topic = topic
        self.interval = interval
        self.running = False

        # Setup logging
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        logging.basicConfig(
            level=getattr(logging, log_level, logging.INFO),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        self.logger = logging.getLogger(f"sensor-{sensor_id}")

        # Setup Kafka producer
        producer_config = {
            "bootstrap.servers": kafka_brokers,
            "client.id": f"sensor-{sensor_id}",
            "acks": "all",
            "retries": 3,
            "compression.type": "snappy",
        }

        try:
            self.producer = Producer(producer_config)
            self.logger.info(
                f"Kafka producer initialized for {sensor_type} sensor {sensor_id}"
            )
        except Exception as e:
            self.logger.error(f"Failed to initialize Kafka producer: {e}")
            raise

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        # Sensor configuration based on type
        self.sensor_config = self._get_sensor_config(sensor_type)
        self.reading_count = 0

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.stop()

    def _get_sensor_config(self, sensor_type: str) -> Dict[str, Any]:
        """Get configuration for specific sensor type with environment overrides."""
        configs = {
            "temperature": {
                "base_value": 25.0,
                "min_value": 15.0,
                "max_value": 45.0,
                "unit": "°C",
                "warning_threshold": float(
                    os.getenv("TEMPERATURE_WARNING_THRESHOLD", "35.0")
                ),
                "critical_threshold": float(
                    os.getenv("TEMPERATURE_CRITICAL_THRESHOLD", "40.0")
                ),
                "noise_factor": 2.0,
            },
            "vibration": {
                "base_value": 2.0,
                "min_value": 0.5,
                "max_value": 8.0,
                "unit": "mm/s",
                "warning_threshold": float(
                    os.getenv("VIBRATION_WARNING_THRESHOLD", "5.0")
                ),
                "critical_threshold": float(
                    os.getenv("VIBRATION_CRITICAL_THRESHOLD", "7.0")
                ),
                "noise_factor": 0.5,
            },
            "energy": {
                "base_value": 100.0,
                "min_value": 50.0,
                "max_value": 200.0,
                "unit": "kW",
                "warning_threshold": 150.0,
                "critical_threshold": 180.0,
                "noise_factor": 10.0,
                # For energy, we use anomaly threshold differently
                "anomaly_threshold": float(
                    os.getenv("ENERGY_ANOMALY_THRESHOLD", "20.0")
                ),
            },
            "humidity": {
                "base_value": 45.0,
                "min_value": 30.0,
                "max_value": 70.0,
                "unit": "%",
                "warning_threshold": 60.0,
                "critical_threshold": 65.0,
                "noise_factor": 5.0,
            },
            "pressure": {
                "base_value": 1013.25,
                "min_value": 980.0,
                "max_value": 1050.0,
                "unit": "hPa",
                "warning_threshold": 1040.0,
                "critical_threshold": 1045.0,
                "noise_factor": 15.0,
            },
        }

        return configs.get(sensor_type, configs["temperature"])

    def generate_sensor_value(self) -> float:
        """Generate a realistic sensor value with some variation."""
        config = self.sensor_config

        # Base value with some time-based variation
        time_factor = time.time() / 3600  # Hourly cycle
        base_variation = (
            config["base_value"] * 0.1 * (0.5 + 0.5 * (time_factor % 24) / 24)
        )

        # Add random noise
        noise = random.gauss(0, config["noise_factor"])

        # Deliberate alert generation (15% warning, 5% critical)
        alert_roll = random.random()
        if alert_roll < 0.05:  # 5% chance for critical alert
            # Generate value near or above critical threshold
            value = config["critical_threshold"] + random.uniform(-2, 10)
            self.logger.debug(f"Generated CRITICAL value: {value}")
        elif alert_roll < 0.20:  # 15% chance for warning alert
            # Generate value near or above warning threshold
            value = config["warning_threshold"] + random.uniform(-1, 8)
            self.logger.debug(f"Generated WARNING value: {value}")
        else:
            # Normal operation with occasional spikes (5% chance)
            if random.random() < 0.05:
                spike_factor = random.uniform(1.2, 1.8)
                noise *= spike_factor

            value = config["base_value"] + base_variation + noise
            self.logger.debug(f"Generated NORMAL value: {value}")

        # Clamp to realistic range
        final_value = max(config["min_value"], min(config["max_value"], value))
        self.logger.debug(f"Final value after clamping: {final_value}")
        return final_value

    def create_sensor_reading(self) -> Dict[str, Any]:
        """Create a sensor reading message."""
        value = self.generate_sensor_value()
        config = self.sensor_config

        # Determine alert level
        alert_level = "normal"
        if value >= config["critical_threshold"]:
            alert_level = "critical"
        elif value >= config["warning_threshold"]:
            alert_level = "warning"

        reading = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "sensor_id": self.sensor_id,
            "sensor_type": self.sensor_type,
            "location": {
                "factory_section": os.getenv("FACTORY_SECTION", "production"),
                "machine_id": os.getenv("MACHINE_ID", f"machine-{self.sensor_id[-3:]}"),
                "zone": os.getenv("ZONE", "zone-a"),
            },
            "value": round(value, 2),
            "unit": config["unit"],
            "alert_level": alert_level,
            "quality": 1.0,
            "metadata": {
                "reading_count": self.reading_count,
                "warning_threshold": config["warning_threshold"],
                "critical_threshold": config["critical_threshold"],
            },
        }

        self.reading_count += 1
        return reading

    def publish_reading(self, reading: Dict[str, Any]) -> bool:
        """Publish sensor reading to Kafka using round-robin partitioning."""
        try:
            # Remove message key to enable round-robin partitioning for better load balancing
            # Each message will be distributed evenly across all partitions
            message_value = json.dumps(reading)

            self.producer.produce(
                topic=self.topic,
                key=None,  # No key = round-robin partitioning
                value=message_value,
                callback=self._delivery_callback,
            )

            # Poll for delivery reports
            self.producer.poll(0)

            self.logger.info(
                f"Published {self.sensor_type} reading: {reading['value']}{reading['unit']} "
                f"(alert: {reading['alert_level']})"
            )
            return True

        except Exception as e:
            self.logger.error(f"Failed to publish reading: {e}")
            return False

    def _delivery_callback(self, err, msg):
        """Callback for message delivery reports."""
        if err is not None:
            self.logger.error(f"Message delivery failed: {err}")
        else:
            self.logger.debug(f"Message delivered to {msg.topic()} [{msg.partition()}]")

    async def run(self):
        """Main sensor loop."""
        self.running = True
        self.logger.info(
            f"Starting {self.sensor_type} sensor {self.sensor_id} "
            f"(interval: {self.interval}s, topic: {self.topic})"
        )

        try:
            while self.running:
                start_time = time.time()

                # Generate and publish reading
                reading = self.create_sensor_reading()
                self.publish_reading(reading)

                # Sleep for the remaining interval time
                elapsed = time.time() - start_time
                sleep_time = max(0, self.interval - elapsed)

                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)

        except Exception as e:
            self.logger.error(f"Error in sensor loop: {e}")
        finally:
            self.cleanup()

    def stop(self):
        """Stop the sensor."""
        self.logger.info("Stopping sensor...")
        self.running = False

    def cleanup(self):
        """Clean up resources."""
        try:
            if self.producer:
                self.logger.info("Flushing remaining messages...")
                remaining = self.producer.flush(timeout=10)
                if remaining > 0:
                    self.logger.warning(f"{remaining} messages not delivered")

            self.logger.info(
                f"Sensor {self.sensor_id} stopped. Total readings: {self.reading_count}"
            )

        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")


async def main():
    """Main function."""
    # Get configuration from environment
    sensor_id = os.getenv("SENSOR_ID", f"sensor-{random.randint(1000, 9999)}")
    sensor_type = os.getenv("SENSOR_TYPE", "temperature")
    kafka_brokers = os.getenv("KAFKA_BROKERS", "kafka1:29092,kafka2:29092,kafka3:29092")
    topic = os.getenv("SENSOR_TOPIC", "sensor-data")
    interval = float(os.getenv("SAMPLING_INTERVAL", "5.0"))

    # Create and run sensor
    sensor = SensorProducer(
        sensor_id=sensor_id,
        sensor_type=sensor_type,
        kafka_brokers=kafka_brokers,
        topic=topic,
        interval=interval,
    )

    try:
        await sensor.run()
    except KeyboardInterrupt:
        sensor.logger.info("Sensor stopped by user")
    finally:
        sensor.stop()


if __name__ == "__main__":
    asyncio.run(main())
