filepoller.py

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


publisher.py

import os
import json
import mysql.connector
import time
from mysql.connector import Error
from kafka import KafkaConsumer

# Environment variables for Kafka and MySQL
kafka_topic = os.getenv('KAFKA_TOPIC', 'employee-data')
kafka_bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
mysql_host = os.getenv('MYSQL_HOST', 'mysql')
mysql_database = os.getenv('MYSQL_DATABASE', 'employee_kafka_db')
mysql_user = os.getenv('MYSQL_USER', 'root')
mysql_password = os.getenv('MYSQL_PASSWORD', '12345678@Lrs')

def connect_to_mysql():
    """Connect to the MySQL database with retry logic."""
    connection = None
    while connection is None:
        try:
            connection = mysql.connector.connect(
                host=mysql_host,
                database=mysql_database,
                user=mysql_user,
                password=mysql_password
            )
            print("Successfully connected to MySQL")
        except Error as e:
            print(f"Error connecting to MySQL: {e}")
            print("Retrying in 5 seconds...")
            time.sleep(5)
    return connection

def create_table(cursor):
    """Create the kafka_emp table if it doesn't exist."""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS kafka_emp (
            id INT AUTO_INCREMENT PRIMARY KEY,
            employee_id VARCHAR(255),
            name VARCHAR(255),
            department VARCHAR(255),
            salary VARCHAR(255)
        )
    """)

def insert_employee(cursor, employee_data):
    """Insert a new employee record into the kafka_emp table."""
    cursor.execute("""
        INSERT INTO kafka_emp (employee_id, name, department, salary)
        VALUES (%s, %s, %s, %s)
    """, (employee_data['Employee ID'], employee_data['Name'], employee_data['Department'], employee_data['Salary']))

def main():
    # Connect to MySQL with retry logic
    connection = connect_to_mysql()
    cursor = connection.cursor()
    create_table(cursor)

    # Set up Kafka consumer
    consumer = KafkaConsumer(
        kafka_topic,
        bootstrap_servers=kafka_bootstrap_servers,
        auto_offset_reset='earliest',
        value_deserializer=lambda v: json.loads(v.decode('utf-8'))
    )

    for message in consumer:
        try:
            print(f"Received message: {message.value}")
            insert_employee(cursor, message.value)
            connection.commit()
        except json.JSONDecodeError as e:
            print(f"Failed to decode JSON message: {e}")
            continue  # Skip invalid messages

    cursor.close()
    connection.close()

if __name__ == "__main__":
    main()




version: '3.8'

services:
  zookeeper:
    image: confluentinc/cp-zookeeper:7.2.1
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000

  kafka:
    image: confluentinc/cp-kafka:7.2.1
    depends_on:
      - zookeeper
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
    ports:
      - "9092:9092"

  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: 12345678@Lrs
      MYSQL_DATABASE: employee_kafka_db
    ports:
      - "3307:3306"
    volumes:
      - mysql_data:/var/lib/mysql

  file-poller:
    build: ./file_poller
    volumes:
      - ./data:/data
    environment:
      CSV_FILE_PATH: /data/employee_data.csv
      KAFKA_BOOTSTRAP_SERVERS: kafka:9092
      KAFKA_TOPIC: employee-data
    depends_on:
      - kafka
    entrypoint: ["sh", "-c", "sleep 40 && python file_poller.py"]  # Increased to 40 seconds

  publisher:
    build: ./publisher
    environment:
      KAFKA_BOOTSTRAP_SERVERS: kafka:9092
      KAFKA_TOPIC: employee-data
      MYSQL_HOST: mysql
      MYSQL_DATABASE: employee_kafka_db
      MYSQL_USER: root
      MYSQL_PASSWORD: 12345678@Lrs
    depends_on:
      - kafka
      - mysql
    entrypoint: ["sh", "-c", "sleep 40 && python publisher.py"]  # Increased to 40 seconds

volumes:
  mysql_data:

