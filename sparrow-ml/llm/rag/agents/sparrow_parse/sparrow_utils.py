import json
from typing import Any, Dict, List, Union


def is_valid_json(json_string: str) -> bool:
    """
    Check if a string is a valid JSON format.

    Args:
        json_string (str): The JSON string to validate.

    Returns:
        bool: True if the JSON string is valid, False otherwise.
    """
    try:
        json.loads(json_string)
        return True
    except json.JSONDecodeError as e:
        print("JSONDecodeError:", e)
        return False


def extract_keys(data: Any, keys: List[str]) -> List[str]:
    """
    Recursively extract unique keys from a dictionary or a list of dictionaries.

    Args:
        data (Any): The JSON data (dict, list, or other types).
        keys (List[str]): A list to store extracted keys.

    Returns:
        List[str]: The list of unique keys.
    """
    if isinstance(data, dict):
        for key, value in data.items():
            if key not in keys:
                keys.append(key)
            extract_keys(value, keys)
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                extract_keys(item, keys)
    return keys


def get_json_keys_as_string(json_string: str) -> str:
    """
    Extract all unique keys from a JSON string and return them as a comma-separated string.

    Args:
        json_string (str): The input JSON string.

    Returns:
        str: Comma-separated string of unique keys, or an empty string for invalid JSON.
    """
    try:
        json_data = json.loads(json_string)

        # If the input is a list, merge all dictionary keys
        if isinstance(json_data, list):
            merged_dict = {}
            for item in json_data:
                if isinstance(item, dict):
                    merged_dict.update(item)
            json_data = merged_dict

        # Extract keys and return them as a string
        keys = extract_keys(json_data, [])
        return ', '.join(keys)

    except json.JSONDecodeError:
        print("Invalid JSON string.")
        return ''


def add_message_to_data(data: Union[Dict, List], key: str, message: Any) -> Dict:
    """
    Add a key-value pair to a dictionary or wrap a list in a dictionary.

    Args:
        data (Union[Dict, List]): The input data (either a dictionary or list).
        key (str): The key to add.
        message (Any): The value to associate with the key.

    Returns:
        Dict: The modified data.
    """
    if isinstance(data, dict):
        data[key] = message
    elif isinstance(data, list):
        data = {"data": data, key: message}
    else:
        raise TypeError("Data must be a dictionary or a list.")
    return data


def add_validation_message(data: Union[Dict, List], message: str) -> Dict:
    """
    Add a validation message to the data.

    Args:
        data (Union[Dict, List]): The input data.
        message (str): The validation message.

    Returns:
        Dict: The modified data.
    """
    return add_message_to_data(data, "valid", message)


def add_page_number(data: Union[Dict, List], page: int) -> Dict:
    """
    Add a page number to the data.

    Args:
        data (Union[Dict, List]): The input data.
        page (int): The page number.

    Returns:
        Dict: The modified data.
    """
    return add_message_to_data(data, "page", page)
