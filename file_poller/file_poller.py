import os
import time
import csv
import hashlib
import json  # Ensure JSON is imported
from kafka import KafkaProducer

csv_file_path = os.getenv('CSV_FILE_PATH', '/data/employee_data.csv')
kafka_topic = os.getenv('KAFKA_TOPIC', 'employee-data')
kafka_bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')

# Initialize a set to track hashes of published rows
published_hashes = set()

def hash_row(row):
    """Generate a hash for a CSV row."""
    row_string = ','.join([str(value) for value in row.values()])
    return hashlib.md5(row_string.encode('utf-8')).hexdigest()

def read_csv_and_send_to_kafka(producer):
    with open(csv_file_path, mode='r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            row_hash = hash_row(row)
            if row_hash not in published_hashes:
                producer.send(kafka_topic, value=json.dumps(row).encode('utf-8'))  # Serialize as JSON
                producer.flush()
                published_hashes.add(row_hash)

def main():
    producer = KafkaProducer(
        bootstrap_servers=kafka_bootstrap_servers,
        value_serializer=lambda v: v
    )

    last_modified_time = None
    while True:
        modified_time = os.path.getmtime(csv_file_path)
        if last_modified_time is None or modified_time > last_modified_time:
            read_csv_and_send_to_kafka(producer)
            last_modified_time = modified_time
        time.sleep(10)

if __name__ == "__main__":
    main()
