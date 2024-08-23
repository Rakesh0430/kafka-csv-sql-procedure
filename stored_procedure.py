import mysql.connector
import requests
import json
import random
from faker import Faker

# Database connection details
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '12345678@Lrs',
    'database': 'lodem'
}

# Placeholder REST API endpoint (mock)
api_url = "https://jsonplaceholder.typicode.com/posts"  # Mock API for testing

# Function to connect to the database and fetch data using a stored procedure
def fetch_employee_data():
    try:
        # Connect to the database
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        # Execute the stored procedure (placeholder name)
        cursor.callproc('sp_get_employees')  # Placeholder stored procedure name
        
        # Fetch the result sets
        employees = []
        for result in cursor.stored_results():
            employees = result.fetchall()
        
        return employees
    
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return []
    
    finally:
        cursor.close()
        conn.close()

# Function to dynamically generate employee data (in case of no data or for testing)
def generate_dynamic_employee_data(num_employees=5):
    fake = Faker()
    employees = []
    
    for _ in range(num_employees):
        employee = {
            'employee_id': random.randint(1000, 9999),
            'first_name': fake.first_name(),
            'last_name': fake.last_name(),
            'email': fake.email(),
            'department': random.choice(['HR', 'Engineering', 'Sales', 'Marketing']),
            'salary': random.randint(40000, 120000),
            'hire_date': fake.date_this_decade().isoformat()
        }
        employees.append(employee)
    
    return employees

# Function to send employee data to the REST API
def send_employee_data_to_api(employees):
    headers = {'Content-Type': 'application/json'}
    
    for employee in employees:
        try:
            response = requests.post(api_url, headers=headers, data=json.dumps(employee))
            
            if response.status_code == 201:  # Assuming 201 is the success status code
                print(f"Successfully sent employee data: {employee['employee_id']}")
            else:
                print(f"Failed to send employee data: {employee['employee_id']}, Status Code: {response.status_code}, Response: {response.text}")
        
        except requests.exceptions.RequestException as e:
            print(f"Error sending employee data: {employee['employee_id']}, Error: {e}")

# Main function to execute the process
def main():
    # Fetch data from the database
    employees = fetch_employee_data()
    
    # If no data is fetched, generate dynamic employee data
    if not employees:
        print("No data fetched from the database. Generating dynamic employee data...")
        employees = generate_dynamic_employee_data()
    
    # Send the data to the REST API
    send_employee_data_to_api(employees)

if __name__ == "__main__":
    main()
