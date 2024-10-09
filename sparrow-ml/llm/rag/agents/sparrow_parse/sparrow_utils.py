import json


def is_valid_json(json_string):
    try:
        json.loads(json_string)
        return True
    except json.JSONDecodeError as e:
        print("JSONDecodeError:", e)
        return False


def get_json_keys_as_string(json_string):
    try:
        # Load the JSON string into a Python object
        json_data = json.loads(json_string)

        # If the input is a list, treat it like a dictionary by merging all the keys
        if isinstance(json_data, list):
            merged_dict = {}
            for item in json_data:
                if isinstance(item, dict):
                    merged_dict.update(item)
            json_data = merged_dict  # Now json_data is a dictionary

        # A helper function to recursively gather keys while preserving order
        def extract_keys(data, keys):
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, dict):
                        # Recursively extract from nested dictionaries
                        extract_keys(value, keys)
                    elif isinstance(value, list):
                        # Process each dictionary inside the list
                        for item in value:
                            if isinstance(item, dict):
                                extract_keys(item, keys)
                    else:
                        if key not in keys:
                            keys.append(key)
            return keys

        # List to hold the keys in order
        keys = []

        # Process the top-level dictionary first
        extract_keys(json_data, keys)

        # Join and return the keys as a comma-separated string
        return ', '.join(keys)

    except json.JSONDecodeError:
        print("Invalid JSON string.")
        return ''