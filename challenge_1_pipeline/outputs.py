import sqlite3
import redis
import json


def init_db(db_path="pipeline.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS processed_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            data TEXT,
            aggregated_value REAL
        )
    """)
    conn.commit()
    conn.close()


def init_redis(host="localhost", port=6379):
    """Initialize Redis connection."""
    return redis.Redis(host=host, port=port, decode_responses=True)


def batch_write_db(records, batch_size=100, db_path="pipeline.db"):
    """Write records to SQLite in batches."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    batch = []
    count = 0

    for record in records:
        batch.append((
            record.get('timestamp'),
            json.dumps(record.get('data')),
            record.get('aggregated_value')
        ))
        count += 1

        if len(batch) >= batch_size:
            cursor.executemany(
                "INSERT INTO processed_data (timestamp, data, aggregated_value) VALUES (?, ?, ?)",
                batch
            )
            conn.commit()
            batch = []

    # Write remaining records
    if batch:
        cursor.executemany(
            "INSERT INTO processed_data (timestamp, data, aggregated_value) VALUES (?, ?, ?)",
            batch
        )
        conn.commit()

    conn.close()
    return count


def batch_write_queue(records, queue_name="processed_data", redis_client=None):
    """Write records to Redis queue in batches."""
    if redis_client is None:
        redis_client = init_redis()

    count = 0
    for record in records:
        redis_client.rpush(queue_name, json.dumps(record))
        count += 1

    return count