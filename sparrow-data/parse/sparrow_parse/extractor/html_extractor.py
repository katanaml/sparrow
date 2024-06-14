from rich import print
from sentence_transformers import SentenceTransformer, util
from bs4 import BeautifulSoup
import json
from rich.progress import Progress, SpinnerColumn, TextColumn
from .extractor_helper import merge_html_table_headers
from .extractor_helper import clean_html_table_header_names
import re


class HTMLExtractor(object):
    def __init__(self):
        pass

    def read_data(self, target_columns, data, column_keywords=None, group_by_rows=True, update_targets=False,
                  local=True, debug=False):
        answer = {}

        json_result, targets_unprocessed = [], []

        i = 0
        for table in data:
            if not target_columns:
                break

            i += 1
            json_result, targets_unprocessed = self.read_data_from_table(target_columns, table, column_keywords,
                                                                         group_by_rows, local, debug)
            answer = self.add_answer_section(answer, "items" + str(i), json_result)

            if update_targets:
                target_columns = targets_unprocessed

        answer = self.format_json_output(answer)

        return answer, targets_unprocessed

    def read_data_from_table(self, target_columns, data, column_keywords=None, group_by_rows=True, local=True, debug=False):
        data = self.invoke_pipeline_step(
            lambda: merge_html_table_headers(data, column_keywords, debug),
            "Merging HTML table headers...",
            local
        )

        data = self.invoke_pipeline_step(
            lambda: clean_html_table_header_names(data),
            "Cleaning HTML table headers...",
            local
        )

        columns = self.get_table_column_names(data)

        if debug:
            print("\n")
            print(f"Columns: {columns}")
            print(f"Target columns: {target_columns}")

        indices, targets, targets_unprocessed = self.invoke_pipeline_step(
            lambda: self.calculate_similarity(columns, target_columns, debug),
            "Calculating cosine similarity between columns and target values...",
            local
        )

        if debug:
            print(f"Unprocessed targets: {targets_unprocessed}")

        # Extracting data
        extracted_data = self.invoke_pipeline_step(
            lambda: self.extract_columns_from_table(data, indices, targets, group_by_rows),
            "Extracting data from the table...",
            local
        )

        json_result = self.convert_to_json(extracted_data)

        return json_result, targets_unprocessed

    def calculate_similarity(self, columns, target_columns, debug):
        model = SentenceTransformer('all-mpnet-base-v2')

        # Compute embeddings for columns and target values
        column_embeddings = model.encode(columns)
        target_embeddings = model.encode(target_columns)

        # List to store indices of the most similar columns
        most_similar_indices = {}
        targets_unprocessed = []

        # Calculate cosine similarity between each column and target value
        similarity_scores = util.pytorch_cos_sim(column_embeddings, target_embeddings)

        # Find the most similar column for each target value and provide the order ID
        for idx, target in enumerate(target_columns):
            similarities = similarity_scores[:, idx]
            most_similar_idx = similarities.argmax().item()
            most_similar_column = columns[most_similar_idx]
            similarity_score = similarities[most_similar_idx].item()
            if similarity_score > 0.3:
                if most_similar_idx in most_similar_indices:
                    if similarity_score > most_similar_indices[most_similar_idx][1]:
                        targets_unprocessed.append(most_similar_indices[most_similar_idx][0])
                        most_similar_indices[most_similar_idx] = (target, similarity_score)
                    else:
                        targets_unprocessed.append(target)
                else:
                    most_similar_indices[most_similar_idx] = (target, similarity_score)
            else:
                targets_unprocessed.append(target)
            if debug:
                print(
                    f"The most similar column to '{target}' is '{most_similar_column}' with a similarity score of {similarity_score:.4f} and order ID {most_similar_idx}")

        most_similar_indices = dict(sorted(most_similar_indices.items()))

        indices = []
        targets = []

        for idx, (target, _) in most_similar_indices.items():
            indices.append(idx)
            targets.append(target)

        if debug:
            print()
            for idx, (target, score) in most_similar_indices.items():
                print(f"Target: '{target}', Column: '{columns[idx]}', Column ID: {idx}, Score: {score:.4f}")
            print()

        return indices, targets, targets_unprocessed

    def extract_columns_from_table(self, html_table, column_ids, target_columns, group_by_rows=False):
        soup = BeautifulSoup(html_table, 'html.parser')
        table = soup.find('table')

        if group_by_rows:
            # Initialize a list to store each row's data as a dictionary
            extracted_data = []
        else:
            # Initialize the extracted data with custom column names
            extracted_data = {target_columns[i]: [] for i in range(len(column_ids))}

        # Extract row information
        rows = table.find_all('tr')

        for row in rows:
            # Skip the header row
            if row.find_all('th'):
                continue

            cells = row.find_all('td')
            if cells:  # Ensure the row contains data cells
                if group_by_rows:
                    row_data = {}
                    for idx, col_id in enumerate(column_ids):
                        value = cells[col_id].text.strip() if col_id < len(cells) else ''
                        value = value.replace('|', '').strip()
                        row_data[target_columns[idx]] = value
                    extracted_data.append(row_data)
                else:
                    for idx, col_id in enumerate(column_ids):
                        value = cells[col_id].text.strip() if col_id < len(cells) else ''
                        value = value.replace('|', '').strip()
                        extracted_data[target_columns[idx]].append(value)

        return extracted_data

    def convert_to_json(self, extracted_data):
        return json.dumps(extracted_data, indent=4)

    def get_table_column_names(self, html_table):
        """
        Extract column names from an HTML table.

        Args:
        html_table (str): The HTML content of the table.

        Returns:
        list: A list of column names.
        """
        # Parse the HTML content using BeautifulSoup with html.parser
        soup = BeautifulSoup(html_table, 'html.parser')

        # Find the <thead> tag
        thead = soup.find('thead')

        # Extract column names into a list
        column_names = [th.get_text() for th in thead.find_all('th')]

        return column_names

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

    def add_answer_section(self, answer, section_name, answer_table):
        if not isinstance(answer, dict):
            raise ValueError("The answer should be a dictionary.")

        # Parse answer_table if it is a JSON string
        if isinstance(answer_table, str):
            answer_table = json.loads(answer_table)

        answer[section_name] = answer_table
        return answer

    def format_json_output(self, answer):
        formatted_json = json.dumps(answer, indent=4)
        formatted_json = formatted_json.replace('", "', '",\n"')
        formatted_json = formatted_json.replace('}, {', '},\n{')
        return formatted_json


if __name__ == "__main__":
    # to run for debugging, navigate to sparrow_parse and run the following command:
    # python -m extractor.html_extractor

    # with open('data/invoice_1_table.txt', 'r') as file:
    #     file_content = file.read()
    #
    # file_content = file_content.strip()[1:-1].strip()
    # data_list = re.split(r"',\s*'", file_content)
    # data_list = [item.strip(" '") for item in data_list]

    extractor = HTMLExtractor()

    # answer, targets_unprocessed = extractor.read_data(
    #     ['description', 'qty', 'net_price', 'net_worth', 'vat', 'gross_worth'],
    #     # ['transaction_date', 'value_date', 'description', 'cheque', 'withdrawal', 'deposit', 'balance',
    #     #  'deposits', 'account_number', 'od_limit', 'currency_balance', 'sgd_balance', 'maturity_date'],
    #     data_list,
    #     None,
    #     # ['deposits', 'account_number', 'od_limit', 'currency_balance', 'sgd_balance', 'transaction_date',
    #     #  'value_date', 'description', 'cheque', 'withdrawal', 'deposit', 'balance', 'maturity_date'],
    #     True,
    #     True,
    #     True,
    #     True)
    #
    # print(answer)
    # print(targets_unprocessed)
