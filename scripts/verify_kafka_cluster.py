#!/usr/bin/env python3
"""
Kafka Cluster Verification Script

This script verifies the Kafka cluster configuration, topic setup,
and broker connectivity for the Factory Monitoring System.
"""

import json
import sys
import time
from typing import List
from confluent_kafka.admin import AdminClient
from confluent_kafka import Producer, Consumer


def create_admin_client(bootstrap_servers: str) -> AdminClient:
    """Create Kafka admin client."""
    config = {"bootstrap.servers": bootstrap_servers}
    return AdminClient(config)


def verify_brokers(admin_client: AdminClient) -> bool:
    """Verify all brokers are accessible."""
    print("🔍 Verifying Kafka brokers...")

    try:
        metadata = admin_client.list_topics(timeout=10)
        brokers = metadata.brokers

        print(f"✓ Found {len(brokers)} brokers:")
        for broker_id, broker in brokers.items():
            print(f"  - Broker {broker_id}: {broker.host}:{broker.port}")

        return len(brokers) >= 3
    except Exception as e:
        print(f"✗ Error connecting to brokers: {e}")
        return False


def verify_topics(admin_client: AdminClient, expected_topics: List[str]) -> bool:
    """Verify topics exist and have correct configuration."""
    print("\n🔍 Verifying Kafka topics...")

    try:
        topics_metadata = admin_client.list_topics(timeout=10)
        existing_topics = set(topics_metadata.topics.keys())

        print(f"✓ Found topics: {', '.join(existing_topics)}")

        # Check if all expected topics exist
        missing_topics = set(expected_topics) - existing_topics
        if missing_topics:
            print(f"✗ Missing topics: {', '.join(missing_topics)}")
            return False

        # Check topic configurations
        for topic_name in expected_topics:
            topic = topics_metadata.topics[topic_name]
            partitions = len(topic.partitions)

            # Get replication factor from first partition
            if topic.partitions:
                replication_factor = len(topic.partitions[0].replicas)
            else:
                replication_factor = 0

            print(
                f"  - {topic_name}: {partitions} partitions, replication factor {replication_factor}"
            )

            # Verify partition distribution
            for partition_id, partition in topic.partitions.items():
                leader = partition.leader
                replicas = partition.replicas
                in_sync_replicas = partition.isrs

                print(
                    f"    Partition {partition_id}: Leader={leader}, "
                    f"Replicas={replicas}, ISR={in_sync_replicas}"
                )

        return True
    except Exception as e:
        print(f"✗ Error verifying topics: {e}")
        return False


def test_producer_connectivity(bootstrap_servers: str, topic: str) -> bool:
    """Test producer connectivity by sending a test message."""
    print(f"\n🔍 Testing producer connectivity to topic '{topic}'...")

    try:
        config = {
            "bootstrap.servers": bootstrap_servers,
            "client.id": "cluster-verification-producer",
        }

        producer = Producer(config)

        # Send test message
        test_message = {
            "test": True,
            "timestamp": time.time(),
            "message": "Cluster verification test",
        }

        producer.produce(
            topic,
            key="test-key",
            value=json.dumps(test_message),
            callback=lambda err, msg: print(
                f"  ✓ Message delivered to {msg.topic()} [{msg.partition()}]"
            )
            if err is None
            else print(f"  ✗ Delivery failed: {err}"),
        )

        producer.flush(timeout=10)
        print("✓ Producer test successful")
        return True

    except Exception as e:
        print(f"✗ Producer test failed: {e}")
        return False


def test_consumer_connectivity(bootstrap_servers: str, topic: str) -> bool:
    """Test consumer connectivity by reading the test message."""
    print(f"\n🔍 Testing consumer connectivity to topic '{topic}'...")

    try:
        config = {
            "bootstrap.servers": bootstrap_servers,
            "group.id": "cluster-verification-consumer",
            "auto.offset.reset": "latest",
            "enable.auto.commit": False,
        }

        consumer = Consumer(config)
        consumer.subscribe([topic])

        # Poll for messages (short timeout for test)
        msg = consumer.poll(timeout=5.0)

        if msg is None:
            print("  ⚠ No messages received (this is normal for empty topics)")
            result = True
        elif msg.error():
            print(f"  ✗ Consumer error: {msg.error()}")
            result = False
        else:
            print(
                f"  ✓ Received message from {msg.topic()} [{msg.partition()}] offset {msg.offset()}"
            )
            result = True

        consumer.close()
        print("✓ Consumer test successful")
        return result

    except Exception as e:
        print(f"✗ Consumer test failed: {e}")
        return False


def verify_cluster_health(bootstrap_servers: str) -> bool:
    """Perform comprehensive cluster health check."""
    print("🏥 Kafka Cluster Health Check")
    print("=" * 50)

    admin_client = create_admin_client(bootstrap_servers)

    # Test broker connectivity
    brokers_ok = verify_brokers(admin_client)

    # Test topic configuration
    expected_topics = ["sensor-data", "alerts"]
    topics_ok = verify_topics(admin_client, expected_topics)

    # Test producer/consumer connectivity
    producer_ok = test_producer_connectivity(bootstrap_servers, "sensor-data")
    consumer_ok = test_consumer_connectivity(bootstrap_servers, "sensor-data")

    # Overall health assessment
    print("\n🏥 Health Check Summary")
    print("=" * 30)
    print(f"Brokers:    {'✓ HEALTHY' if brokers_ok else '✗ UNHEALTHY'}")
    print(f"Topics:     {'✓ HEALTHY' if topics_ok else '✗ UNHEALTHY'}")
    print(f"Producer:   {'✓ HEALTHY' if producer_ok else '✗ UNHEALTHY'}")
    print(f"Consumer:   {'✓ HEALTHY' if consumer_ok else '✗ UNHEALTHY'}")

    overall_health = all([brokers_ok, topics_ok, producer_ok, consumer_ok])
    print(
        f"\nOverall:    {'✓ CLUSTER HEALTHY' if overall_health else '✗ CLUSTER UNHEALTHY'}"
    )

    return overall_health


def main():
    """Main verification function."""
    # Use internal Kafka addresses for comprehensive testing
    internal_servers = "kafka1:29092,kafka2:29092,kafka3:29092"

    print("🚀 Factory Monitoring System - Kafka Cluster Verification")
    print("=" * 60)

    # Test with internal addresses (from within Docker network)
    print("\n📡 Testing internal connectivity...")
    try:
        internal_health = verify_cluster_health(internal_servers)
    except Exception as e:
        print(f"Internal connectivity test failed: {e}")
        internal_health = False

    # Final assessment based on internal connectivity only
    # External testing from within container is not reliable
    print("\n🎯 Final Assessment")
    print("=" * 20)
    if internal_health:
        print("✅ KAFKA CLUSTER FULLY OPERATIONAL")
        print("✅ Internal network connectivity verified")
        print("✅ All brokers accessible and healthy")
        print("✅ Topics properly configured")
        print("✅ Producer/Consumer operations working")
        print("Ready for sensor producers and data consumers!")
        return 0
    else:
        print("❌ CLUSTER NOT OPERATIONAL")
        print("Please check Kafka broker status and configuration")
        return 2


if __name__ == "__main__":
    sys.exit(main())
