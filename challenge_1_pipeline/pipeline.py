from collections import deque
from datetime import datetime


def transform_data(records):
    """
    Transform incoming records by adding timestamp and validating structure.
    Uses generator to maintain constant memory usage.
    """
    for record in records:
        print(f"[TRANSFORM] Input record: {record}")
        # Add timestamp if not present
        if 'timestamp' not in record:
            record['timestamp'] = datetime.utcnow().isoformat()

        transformed = {
            'timestamp': record['timestamp'],
            'data': record.get('data', record),  # Use 'data' key if it exists, otherwise use whole record
            'original_size': len(str(record))
        }
        print(f"[TRANSFORM] Output record: {transformed}")

        yield transformed


def aggregate_data(records, window_size=10):
    window = deque(maxlen=window_size)

    for record in records:
        window.append(record)

        # Calculate aggregate metrics over the window
        avg_size = sum(r.get('original_size', 0) for r in window) / len(window)

        # Yield enriched record with aggregation
        enriched = {
            'timestamp': record['timestamp'],
            'data': record['data'],
            'aggregated_value': avg_size,
            'window_count': len(window)
        }

        yield enriched


def process_pipeline(records, window_size=10):
    transformed = transform_data(records)
    aggregated = aggregate_data(transformed, window_size)
    return aggregated