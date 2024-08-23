import csv
import os
import xml.etree.ElementTree as ET
import logging

# Configure logging
logging.basicConfig(filename='xml_generation.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Decorator for error handling and logging
def handle_errors(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.error(f"Error in {func.__name__}: {e}")
            print(f"An error occurred. Please check the log file for details.")
    return wrapper

# 1. Create sample employee data CSV file
@handle_errors
def create_employee_csv(filename):
    data = [
        ['Employee ID', 'Name', 'Department', 'Salary'],
        ['1', 'John', 'Sales', '50000'],
        ['2', 'Jane', 'HR', '60000'],
        ['3', 'Mike', 'IT', '75000'],
        ['4', 'Emily', 'Sales', '55000'],
        ['5', 'David', 'HR', '62000'],
    ]

    with open(filename, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(data)
    logging.info(f"CSV file '{filename}' created successfully.")

# 2. Group data by 'Department'
@handle_errors
def group_data_by_department(filename):
    grouped_data = {}
    with open(filename, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            department = row['Department']
            if department not in grouped_data:
                grouped_data[department] = []
            grouped_data[department].append(row)
    logging.info(f"Data grouped by department from '{filename}'.")
    return grouped_data

# 3. Create XML from grouped data (vertical format)
@handle_errors
def create_xml(grouped_data, output_filename):
    root = ET.Element('Employees')

    all_employees = [emp for employees in grouped_data.values() for emp in employees]

    for employee in all_employees:
        emp_element = ET.SubElement(root, 'Employee')
        for key, value in employee.items():
            ET.SubElement(emp_element, key).text = value

    tree = ET.ElementTree(root)
    ET.indent(tree, space="\t", level=0)
    tree.write(output_filename, encoding='utf-8', xml_declaration=True)

    file_size = os.path.getsize(output_filename)
    logging.info(f"XML file generated at: {output_filename} (Size: {file_size} bytes)")
    print(f"XML file generated at: {output_filename} (Size: {file_size} bytes)")

# Main execution
if __name__ == "__main__":
    csv_filename = 'employee_data_grouped.csv'
    xml_output_folder = 'xml_gen_grouped'
    xml_output_filename = os.path.join(xml_output_folder, 'employee_data.xml')

    # Create CSV if it doesn't exist
    if not os.path.exists(csv_filename):
        create_employee_csv(csv_filename)

    # Create output folder if it doesn't exist
    if not os.path.exists(xml_output_folder):
        os.makedirs(xml_output_folder)

    grouped_data = group_data_by_department(csv_filename)
    create_xml(grouped_data, xml_output_filename)