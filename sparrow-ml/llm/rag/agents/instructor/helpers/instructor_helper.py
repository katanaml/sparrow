from sparrow_parse.extractor.unstructured_processor import UnstructuredProcessor
from sparrow_parse.extractor.markdown_processor import MarkdownProcessor
import json


def execute_sparrow_processor(options, file_path, strategy, model_name, local, debug):
    content, table_content = None, None
    if "unstructured" in options:
        processor = UnstructuredProcessor()
        content, table_content = processor.extract_data(file_path, strategy, model_name,
                                                        ['tables', 'unstructured'], local, debug)
    elif "markdown" in options:
        processor = MarkdownProcessor()
        content, table_content = processor.extract_data(file_path, ['tables', 'markdown'], local, debug)

    return content, table_content


def merge_dicts(json_str1, json_str2):
    # Convert JSON strings to dictionaries
    dict1 = json.loads(json_str1)
    dict2 = json.loads(json_str2)

    merged_dict = dict1.copy()
    for key, value in dict2.items():
        if key in merged_dict and isinstance(merged_dict[key], list) and isinstance(value, list):
            merged_dict[key].extend(value)
        else:
            merged_dict[key] = value
    return merged_dict


def track_query_output(keys, json_data, types):
    # Convert JSON string to dictionary
    data = json.loads(json_data)

    # Initialize the result lists
    result = []
    result_types = []

    # Iterate through each key in the keys array
    for i, key in enumerate(keys):
        # Check if the key is present in the JSON and has a non-empty value
        if key not in data or not data[key].strip():
            result.append(key)
            result_types.append(types[i])

    return result, result_types


def add_answer_page(answer, page_name, answer_page):
    if not isinstance(answer, dict):
        raise ValueError("The answer should be a dictionary.")

    # Parse answer_table if it is a JSON string
    if isinstance(answer_page, str):
        answer_page = json.loads(answer_page)

    answer[page_name] = answer_page
    return answer
