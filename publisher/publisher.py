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
