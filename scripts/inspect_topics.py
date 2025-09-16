#!/usr/bin/env python3
"""
Simple Kafka Topic Inspector

Quick script to inspect topic configurations and partition assignments.
"""

from confluent_kafka.admin import AdminClient


def inspect_topics():
    """Inspect Kafka topics and their configurations."""
    # Use internal Kafka addresses
    config = {"bootstrap.servers": "kafka1:29092,kafka2:29092,kafka3:29092"}
    admin_client = AdminClient(config)

    print("📊 Kafka Topics Inspection")
    print("=" * 40)

    try:
        topics_metadata = admin_client.list_topics(timeout=10)

        for topic_name, topic in topics_metadata.topics.items():
            if not topic_name.startswith("__"):  # Skip internal topics
                print(f"\n🏷️  Topic: {topic_name}")
                print(f"   Partitions: {len(topic.partitions)}")

                for partition_id, partition in topic.partitions.items():
                    repl_factor = len(partition.replicas)
                    print(
                        f"   Partition {partition_id}: Leader={partition.leader}, "
                        f"Replicas={partition.replicas}, RF={repl_factor}"
                    )
                    print(f"                    ISR={partition.isrs}")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    inspect_topics()
