"""
Factory Monitoring Service

Flask-based API service that provides real-time monitoring data
for the distributed sensor monitoring system.
"""

import logging
import os
from flask import Flask, jsonify, render_template
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global database pool
db_pool = None


def init_database():
    """Initialize database connection pool."""
    global db_pool

    try:
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            logger.error("DATABASE_URL environment variable not set")
            return False

        # Create connection pool
        db_pool = SimpleConnectionPool(minconn=1, maxconn=10, dsn=database_url)

        logger.info("Database connection pool initialized successfully")
        return True

    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return False


def get_db_connection():
    """Get database connection from pool."""
    if not db_pool:
        return None

    try:
        return db_pool.getconn()
    except Exception as e:
        logger.error(f"Error getting database connection: {e}")
        return None


def return_db_connection(conn):
    """Return database connection to pool."""
    if db_pool and conn:
        try:
            db_pool.putconn(conn)
        except Exception as e:
            logger.error(f"Error returning database connection: {e}")


@app.route("/")
def dashboard():
    """Serve the main monitoring dashboard."""
    return render_template("dashboard.html")


@app.route("/api/system-status")
def get_system_status():
    """Get current system status overview."""
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Get consumer status
        cursor.execute("""
            SELECT 
                COUNT(*) as total_count,
                COUNT(*) FILTER (WHERE status = 'active' AND last_heartbeat > NOW() - INTERVAL '5 seconds') as active_count,
                MAX(last_heartbeat) as last_activity
            FROM consumer_health
        """)
        consumer_status = cursor.fetchone()

        # Get producer status
        cursor.execute("""
            SELECT 
                COUNT(*) as total_count,
                COUNT(*) FILTER (WHERE status = 'active' AND last_heartbeat > NOW() - INTERVAL '5 seconds') as active_count,
                MAX(last_heartbeat) as last_activity
            FROM producer_health
        """)
        producer_status = cursor.fetchone()

        # Get recent rebalancing events
        cursor.execute("""
            SELECT event_type, consumer_id, partition_number, timestamp_utc
            FROM rebalancing_events 
            WHERE timestamp_utc >= NOW() - INTERVAL '1 hour'
            ORDER BY timestamp_utc DESC
            LIMIT 10
        """)
        rebalancing_events = cursor.fetchall()

        # Build status result
        status_result = {
            "consumers": {
                "active_count": consumer_status["active_count"] or 0,
                "total_count": consumer_status["total_count"] or 0,
                "last_activity": consumer_status["last_activity"].isoformat()
                if consumer_status["last_activity"]
                else None,
            },
            "producers": {
                "active_count": producer_status["active_count"] or 0,
                "total_count": producer_status["total_count"] or 0,
                "last_activity": producer_status["last_activity"].isoformat()
                if producer_status["last_activity"]
                else None,
            },
        }

        rebalancing_result = [
            {
                "event_type": event["event_type"],
                "consumer_id": event["consumer_id"],
                "partition_number": event["partition_number"],
                "timestamp": event["timestamp_utc"].isoformat(),
            }
            for event in rebalancing_events
        ]

        return jsonify(
            {"status": status_result, "rebalancing_events": rebalancing_result}
        )

    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        return_db_connection(conn)


@app.route("/api/real-time-metrics")
def get_real_time_metrics():
    """Get real-time throughput and distribution metrics."""
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Get consumer throughput (last 10 minutes)
        cursor.execute("""
            SELECT 
                processed_by_consumer as component_id,
                COUNT(*) as value
            FROM sensor_readings 
            WHERE processing_timestamp >= NOW() - INTERVAL '10 minutes'
                AND processed_by_consumer IS NOT NULL
            GROUP BY processed_by_consumer
            ORDER BY component_id
        """)
        consumer_throughput = cursor.fetchall()

        # Get producer total messages (for active producers)
        cursor.execute("""
            SELECT 
                ph.producer_id as component_id,
                ph.total_messages_sent as value
            FROM producer_health ph
            WHERE ph.status = 'active' AND ph.last_heartbeat >= NOW() - INTERVAL '5 seconds'
            ORDER BY component_id
        """)
        producer_throughput = cursor.fetchall()

        # Get partition activity (last 10 minutes)
        cursor.execute("""
            SELECT 
                kafka_partition as partition_number,
                COUNT(*) as message_count
            FROM sensor_readings 
            WHERE processing_timestamp >= NOW() - INTERVAL '10 minutes'
                AND kafka_partition IS NOT NULL
            GROUP BY kafka_partition
            ORDER BY kafka_partition
        """)
        partition_activity = cursor.fetchall()

        # Build result
        metrics_result = {
            "consumer_throughput": [
                {"component_id": row["component_id"], "value": row["value"]}
                for row in consumer_throughput
            ],
            "producer_throughput": [
                {"component_id": row["component_id"], "value": row["value"]}
                for row in producer_throughput
            ],
            "partition_activity": {
                str(row["partition_number"]): row["message_count"]
                for row in partition_activity
            },
        }

        return jsonify(metrics_result)

    except Exception as e:
        logger.error(f"Error getting real-time metrics: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        return_db_connection(conn)


@app.route("/api/consumer-health")
def get_consumer_health():
    """Get detailed consumer health information."""
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("""
            SELECT consumer_id, status, assigned_partitions, last_heartbeat,
                   total_messages_processed,
                   CASE 
                       WHEN status = 'active' AND last_heartbeat > NOW() - INTERVAL '5 seconds' THEN 'active'
                       ELSE 'inactive'
                   END as calculated_status
            FROM consumer_health 
            ORDER BY consumer_id
        """)
        consumer_data = cursor.fetchall()

        result = []
        for row in consumer_data:
            result.append(
                {
                    "consumer_id": row["consumer_id"],
                    "status": row["calculated_status"],  # Use calculated status instead of raw status
                    "assigned_partitions": row["assigned_partitions"],
                    "last_heartbeat": row["last_heartbeat"].isoformat(),
                    "total_messages_processed": row["total_messages_processed"],
                }
            )

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error getting consumer health: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        return_db_connection(conn)


@app.route("/api/producer-health")
def get_producer_health():
    """Get detailed producer health information."""
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("""
            SELECT producer_id, sensor_type, status, last_heartbeat,
                   total_messages_sent,
                   CASE 
                       WHEN status = 'active' AND last_heartbeat > NOW() - INTERVAL '5 seconds' THEN 'active'
                       ELSE 'inactive'
                   END as calculated_status
            FROM producer_health 
            ORDER BY producer_id
        """)
        producer_data = cursor.fetchall()

        result = []
        for row in producer_data:
            result.append(
                {
                    "producer_id": row["producer_id"],
                    "sensor_type": row["sensor_type"],
                    "status": row["calculated_status"],  # Use calculated status instead of raw status
                    "last_heartbeat": row["last_heartbeat"].isoformat(),
                    "total_messages_sent": row["total_messages_sent"],
                }
            )

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error getting producer health: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        return_db_connection(conn)


@app.route("/api/recent-alerts")
def get_recent_alerts():
    """Get recent alerts for monitoring."""
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("""
            SELECT alert_id, sensor_id, sensor_type, anomaly_type, severity,
                   sensor_value, sensor_unit, description, detected_by, timestamp_utc
            FROM alerts 
            WHERE timestamp_utc >= NOW() - INTERVAL '2 hours'
            ORDER BY timestamp_utc DESC
            LIMIT 50
        """)
        alerts_data = cursor.fetchall()

        result = []
        for row in alerts_data:
            result.append(
                {
                    "alert_id": row["alert_id"],
                    "sensor_id": row["sensor_id"],
                    "sensor_type": row["sensor_type"],
                    "anomaly_type": row["anomaly_type"],
                    "severity": row["severity"],
                    "sensor_value": float(row["sensor_value"]),
                    "sensor_unit": row["sensor_unit"],
                    "description": row["description"],
                    "detected_by": row["detected_by"],
                    "timestamp": row["timestamp_utc"].isoformat(),
                }
            )

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error getting recent alerts: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        return_db_connection(conn)


@app.route("/api/partition-assignment")
def get_partition_assignment():
    """Get current partition assignment details."""
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Get current partition assignments from consumer health
        cursor.execute("""
            SELECT consumer_id, assigned_partitions, status, last_heartbeat
            FROM consumer_health 
            WHERE status = 'active'
            ORDER BY consumer_id
        """)
        assignment_data = cursor.fetchall()

        # Get recent message counts per partition
        cursor.execute("""
            SELECT kafka_partition, COUNT(*) as message_count
            FROM sensor_readings 
            WHERE processing_timestamp >= NOW() - INTERVAL '5 minutes'
            AND kafka_partition IS NOT NULL
            GROUP BY kafka_partition
            ORDER BY kafka_partition
        """)
        partition_counts = cursor.fetchall()

        result = {"assignments": [], "partition_activity": {}}

        for row in assignment_data:
            result["assignments"].append(
                {
                    "consumer_id": row["consumer_id"],
                    "assigned_partitions": row["assigned_partitions"],
                    "status": row["status"],
                    "last_heartbeat": row["last_heartbeat"].isoformat(),
                }
            )

        for row in partition_counts:
            result["partition_activity"][str(row["kafka_partition"])] = row[
                "message_count"
            ]

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error getting partition assignment: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        return_db_connection(conn)


@app.route("/health")
def health_check():
    """Health check endpoint."""
    conn = get_db_connection()
    if not conn:
        return jsonify(
            {"status": "unhealthy", "reason": "database connection failed"}
        ), 503

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        return jsonify({"status": "healthy"})
    except Exception as e:
        return jsonify({"status": "unhealthy", "reason": str(e)}), 503
    finally:
        return_db_connection(conn)


def main():
    """Main entry point for the monitoring service."""
    # Initialize database
    if not init_database():
        logger.error("Failed to initialize database, exiting")
        return 1

    # Get configuration from environment
    host = os.environ.get("MONITORING_HOST", "0.0.0.0")
    port = int(os.environ.get("MONITORING_PORT", "5000"))
    debug = os.environ.get("DEBUG", "false").lower() == "true"

    logger.info(f"Starting monitoring service on {host}:{port}")
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    main()
