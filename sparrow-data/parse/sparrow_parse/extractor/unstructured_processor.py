import tempfile
import os
from unstructured.partition.pdf import partition_pdf
from unstructured.partition.image import partition_image
import json
from unstructured.staging.base import elements_to_json
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print
from bs4 import BeautifulSoup


class UnstructuredProcessor(object):
    def __init__(self):
        pass

    def extract_data(self, file_path, strategy, model_name, options, langs=['en'], local=True, debug=False):
        # Extracts the elements from the PDF
        elements = self.invoke_pipeline_step(
            lambda: self.process_file(file_path, strategy, model_name, langs),
            "Extracting elements from the document...",
            local
        )

        if debug:
            new_extension = 'json'  # You can change this to any extension you want
            new_file_path = self.change_file_extension(file_path, new_extension)

            content, table_content = self.invoke_pipeline_step(
                lambda: self.load_text_data(elements, new_file_path, options),
                "Loading text data...",
                local
            )
        else:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_file_path = os.path.join(temp_dir, "file_data.json")

                content, table_content = self.invoke_pipeline_step(
                    lambda: self.load_text_data(elements, temp_file_path, options),
                    "Loading text data...",
                    local
                )

        if debug:
            print("Data extracted from the document:")
            print(content)
            print("\n")
            print("Table content extracted from the document:")
            if table_content:
                print(len(table_content))
            print(table_content)

        return content, table_content

    def process_file(self, file_path, strategy, model_name, langs=[]):
        elements = None

        if file_path.lower().endswith('.pdf'):
            elements = partition_pdf(
                filename=file_path,
                strategy=strategy,
                infer_table_structure=True,
                hi_res_model_name=model_name,
                languages=langs
            )
        elif file_path.lower().endswith(('.jpg', '.jpeg', '.png')):
            elements = partition_image(
                filename=file_path,
                strategy=strategy,
                infer_table_structure=True,
                hi_res_model_name=model_name,
                languages=langs
            )

        return elements

    def change_file_extension(self, file_path, new_extension, suffix=None):
        # Check if the new extension starts with a dot and add one if not
        if not new_extension.startswith('.'):
            new_extension = '.' + new_extension

        # Split the file path into two parts: the base (everything before the last dot) and the extension
        # If there's no dot in the filename, it'll just return the original filename without an extension
        base = file_path.rsplit('.', 1)[0]

        # Concatenate the base with the new extension
        if suffix is None:
            new_file_path = base + new_extension
        else:
            new_file_path = base + "_" + suffix + new_extension

        return new_file_path

    def load_text_data(self, elements, file_path, options):
        elements_to_json(elements, filename=file_path)

        content, table_content = None, None

        if options is None:
            content = self.process_json_file(file_path)

        if options and "tables" in options and "unstructured" in options:
            content = self.process_json_file(file_path, "form")

            table_content = self.process_json_file(file_path, "table")

        return content, table_content

    def process_json_file(self, file_path, option=None):
        # Read the JSON file
        with open(file_path, 'r') as file:
            data = json.load(file)

        # Iterate over the JSON data and extract required elements
        extracted_elements = []
        for entry in data:
            if entry["type"] == "Table" and (option is None or option == "table" or option == "form"):
                table_data = entry["metadata"]["text_as_html"]
                if option == "table" and self.table_has_header(table_data):
                    extracted_elements.append(table_data)
                if option is None or option == "form":
                    extracted_elements.append(table_data)
            elif entry["type"] == "Title" and (option is None or option == "form"):
                extracted_elements.append(entry["text"])
            elif entry["type"] == "NarrativeText" and (option is None or option == "form"):
                extracted_elements.append(entry["text"])
            elif entry["type"] == "UncategorizedText" and (option is None or option == "form"):
                extracted_elements.append(entry["text"])
            elif entry["type"] == "ListItem" and (option is None or option == "form"):
                extracted_elements.append(entry["text"])
            elif entry["type"] == "Image" and (option is None or option == "form"):
                extracted_elements.append(entry["text"])

        if option is None or option == "form":
            # Convert list to single string with two new lines between each element
            extracted_data = "\n\n".join(extracted_elements)
            return extracted_data

        return extracted_elements

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

    def table_has_header(self, table_html):
        soup = BeautifulSoup(table_html, 'html.parser')
        table = soup.find('table')

        # Check if the table contains a <thead> tag
        if table.find('thead'):
            return True

        # Check if the table contains any <th> tags inside the table (in case there's no <thead>)
        if table.find_all('th'):
            return True

        return False


if __name__ == "__main__":
    # processor = UnstructuredProcessor()
    # content, table_content = processor.extract_data(
    #     '../sample/fr_train_0.jpg',
    #     'hi_res',
    #     'yolox',
    #     ['tables', 'unstructured'],
    #     ['fr'],
    #     True,
    #     True)
    # print(content)
    # print(table_content)
