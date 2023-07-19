import json
import os
from datetime import datetime


def log_stats(file_path, new_data):
    # Check if the file exists, and read its content
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            try:
                content = json.load(file)
            except json.JSONDecodeError:
                content = []
    else:
        content = []

    # Get the current date and time
    now = datetime.now()
    # Format the date and time as a string
    date_time_string = now.strftime("%Y-%m-%d %H:%M:%S")
    new_data.append(date_time_string)

    # Append the new data to the content
    content.append(new_data)

    # Write the updated content back to the file
    with open(file_path, 'w') as file:
        json.dump(content, file)
