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
