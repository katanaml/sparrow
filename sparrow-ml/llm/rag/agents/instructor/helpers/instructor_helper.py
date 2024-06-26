from sparrow_parse.extractor.unstructured_processor import UnstructuredProcessor
from sparrow_parse.extractor.markdown_processor import MarkdownProcessor
import json
import PyPDF2
from pdf2image import convert_from_path
import os
import tempfile


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


def pre_process_pdf(file_path, convert_to_images):
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()
    output_files = []

    if not convert_to_images:
        # Open the PDF file
        with open(file_path, 'rb') as pdf_file:
            reader = PyPDF2.PdfReader(pdf_file)
            number_of_pages = len(reader.pages)

            # Split the PDF into separate files per page
            for page_num in range(number_of_pages):
                writer = PyPDF2.PdfWriter()
                writer.add_page(reader.pages[page_num])

                output_filename = os.path.join(temp_dir, f'page_{page_num + 1}.pdf')
                with open(output_filename, 'wb') as output_file:
                    writer.write(output_file)
                    output_files.append(output_filename)

        # Return the number of pages, the list of file paths, and the temporary directory
        return number_of_pages, output_files, temp_dir
    else:
        # Convert the PDF to images
        images = convert_from_path(file_path, dpi=400)

        # Save the images to the temporary directory
        for i, image in enumerate(images):
            output_filename = os.path.join(temp_dir, f'page_{i + 1}.jpg')
            image.save(output_filename, 'JPEG')
            output_files.append(output_filename)

            # Save each image to the debug folder
            # debug_output_filename = os.path.join("/Users/andrejb/infra/shared/katana-git/sparrow/sparrow-ml/llm/data/", f'page_{i + 1}.jpg')
            # image.save(debug_output_filename, 'JPEG')

        # Return the number of pages, the list of file paths, and the temporary directory
        return len(images), output_files, temp_dir


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
