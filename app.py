import csv
import xml.etree.ElementTree as ET
import html
import os
import tempfile
import logging
from flask import Flask, request, send_file
from werkzeug.utils import secure_filename
from threading import Thread
import time

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Store temporary files
temp_files = []

def indent(elem, level=0):
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

def csv_to_xml(csv_file, xml_file):
    logger.debug(f"Starting CSV to XML conversion: {csv_file} -> {xml_file}")
    
    # Create the root element of the XML
    root = ET.Element('EmployeeData')
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader, None)  # Read the header row
            
            if not header:
                logger.error("CSV file is empty or has no header row")
                raise ValueError("CSV file is empty or has no header row")
            
            logger.debug(f"CSV Header: {header}")
            
            # Iterate through each row in the CSV
            for i, row in enumerate(reader, start=1):
                logger.debug(f"Processing row {i}: {row}")
                
                # Create a new element for each row
                employee_element = ET.SubElement(root, 'Employee')
                
                # Add the ID as an attribute, ensuring it's not empty
                employee_id = str(i) if i else "unknown"
                employee_element.set('ID', employee_id)
                logger.debug(f"Set Employee ID: {employee_id}")
                
                # Create sub-elements for each column in the row
                for column_name, value in zip(header, row):
                    # Skip empty column names
                    if column_name and column_name.strip():
                        safe_column_name = ''.join(c for c in column_name.strip() if c.isalnum() or c in ('_', '-'))
                        if safe_column_name:
                            column_element = ET.SubElement(employee_element, safe_column_name)
                            # Escape special characters and ensure the value is not empty
                            safe_value = html.escape(value.strip()) if value and value.strip() else " "
                            column_element.text = safe_value
                            logger.debug(f"Added element: {safe_column_name} = {safe_value}")
                        else:
                            logger.warning(f"Skipped invalid column name: {column_name}")
                    else:
                        logger.warning(f"Skipped empty column name in row {i}")
        
        # Indent the XML for pretty printing
        indent(root)
        
        # Write the XML to file
        tree = ET.ElementTree(root)
        tree.write(xml_file, encoding='utf-8', xml_declaration=True)
        logger.debug(f"XML file written successfully: {xml_file}")
        
    except Exception as e:
        logger.error(f"Error during CSV to XML conversion: {str(e)}")
        raise

def cleanup_old_files():
    while True:
        time.sleep(300)  # Wait for 5 minutes
        current_time = time.time()
        for file_path, create_time in temp_files[:]:
            if current_time - create_time > 600:  # If file is older than 10 minutes
                try:
                    os.remove(file_path)
                    temp_files.remove((file_path, create_time))
                    logger.info(f"Cleaned up old file: {file_path}")
                except Exception as e:
                    logger.error(f"Error cleaning up file {file_path}: {str(e)}")

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            logger.warning("No file part in the request")
            return 'No file part'
        file = request.files['file']
        if file.filename == '':
            logger.warning("No selected file")
            return 'No selected file'
        if file:
            filename = secure_filename(file.filename)
            csv_path = os.path.join(tempfile.gettempdir(), filename)
            file.save(csv_path)
            logger.info(f"Saved uploaded file: {csv_path}")
            
            xml_filename = os.path.splitext(filename)[0] + '.xml'
            xml_path = os.path.join(tempfile.gettempdir(), xml_filename)
            
            try:
                csv_to_xml(csv_path, xml_path)
                temp_files.append((csv_path, time.time()))
                temp_files.append((xml_path, time.time()))
                logger.info(f"Conversion successful, sending file: {xml_path}")
                return send_file(xml_path, as_attachment=True)
            except Exception as e:
                logger.error(f"Error during file processing: {str(e)}")
                return f"An error occurred: {str(e)}"
    return '''
    <!doctype html>
    <title>Upload CSV File</title>
    <h1>Upload CSV File</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    '''

if __name__ == '__main__':
    cleanup_thread = Thread(target=cleanup_old_files)
    cleanup_thread.daemon = True
    cleanup_thread.start()
    logger.info("Starting Flask application")
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))