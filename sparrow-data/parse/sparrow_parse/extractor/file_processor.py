import tempfile
import os
from unstructured.partition.pdf import partition_pdf
from unstructured.partition.image import partition_image
import json
from unstructured.staging.base import elements_to_json
from rich.progress import Progress, SpinnerColumn, TextColumn


class FileProcessor(object):
    def __init__(self):
        pass

    def extract_data(self, file_path, strategy, model_name, options, local=True, debug=False):
        # check if string options contains word table
        extract_tables = False
        if options is not None and "tables" in options:
            extract_tables = True

        # Extracts the elements from the PDF
        elements = self.invoke_pipeline_step(
            lambda: self.process_file(file_path, strategy, model_name),
            "Extracting elements from the document...",
            local
        )

        if debug:
            new_extension = 'json'  # You can change this to any extension you want
            new_file_path = self.change_file_extension(file_path, new_extension)

            content = self.invoke_pipeline_step(
                lambda: self.load_text_data(elements, new_file_path, extract_tables),
                "Loading text data...",
                local
            )
        else:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_file_path = os.path.join(temp_dir, "file_data.json")

                content = self.invoke_pipeline_step(
                    lambda: self.load_text_data(elements, temp_file_path, extract_tables),
                    "Loading text data...",
                    local
                )

        return content

    def process_file(self, file_path, strategy, model_name):
        elements = None

        if file_path.lower().endswith('.pdf'):
            elements = partition_pdf(
                filename=file_path,
                strategy=strategy,
                infer_table_structure=True,
                model_name=model_name
            )
        elif file_path.lower().endswith(('.jpg', '.jpeg', '.png')):
            elements = partition_image(
                filename=file_path,
                strategy=strategy,
                infer_table_structure=True,
                model_name=model_name
            )

        return elements

    def change_file_extension(self, file_path, new_extension):
        # Check if the new extension starts with a dot and add one if not
        if not new_extension.startswith('.'):
            new_extension = '.' + new_extension

        # Split the file path into two parts: the base (everything before the last dot) and the extension
        # If there's no dot in the filename, it'll just return the original filename without an extension
        base = file_path.rsplit('.', 1)[0]

        # Concatenate the base with the new extension
        new_file_path = base + new_extension

        return new_file_path

    def load_text_data(self, elements, file_path, extract_tables):
        elements_to_json(elements, filename=file_path)
        text_file = self.process_json_file(file_path, extract_tables)

        with open(text_file, 'r') as file:
            content = file.read()

        return content

    def process_json_file(self, input_data, extract_tables):
        # Read the JSON file
        with open(input_data, 'r') as file:
            data = json.load(file)

        # Iterate over the JSON data and extract required table elements
        extracted_elements = []
        for entry in data:
            if entry["type"] == "Table":
                extracted_elements.append(entry["metadata"]["text_as_html"])
            elif entry["type"] == "Title" and extract_tables is False:
                extracted_elements.append(entry["text"])
            elif entry["type"] == "NarrativeText" and extract_tables is False:
                extracted_elements.append(entry["text"])
            elif entry["type"] == "UncategorizedText" and extract_tables is False:
                extracted_elements.append(entry["text"])

        # Write the extracted elements to the output file
        new_extension = 'txt'  # You can change this to any extension you want
        new_file_path = self.change_file_extension(input_data, new_extension)
        with open(new_file_path, 'w') as output_file:
            for element in extracted_elements:
                output_file.write(element + "\n\n")  # Adding two newlines for separation

        return new_file_path

    def invoke_pipeline_step(self, task_call, task_description, local):
        if local:
            with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    transient=False,
            ) as progress:
                progress.add_task(description=task_description, total=None)
                ret = task_call()
        else:
            print(task_description)
            ret = task_call()

        return ret


# if __name__ == "__main__":
#     processor = FileProcessor()
#     content = processor.extract_data('/Users/andrejb/infra/shared/katana-git/sparrow/sparrow-ml/llm/data/invoice_1.pdf',
#                                      'hi_res',
#                                      'yolox',
#                                      'tables',
#                                      False,
#                                      True)
#     processor.extract_data("/Users/andrejb/Documents/work/lifung/lemming_test/C16E150001_SUPINV.pdf")
#     processor.extract_data("/Users/andrejb/Documents/work/epik/bankstatement/OCBC_1_single.pdf")
#     print(content)
