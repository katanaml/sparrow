import pymupdf4llm
import pandas as pd
import re
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print
from bs4 import BeautifulSoup


class MarkdownProcessor(object):
    def __init__(self):
        pass

    def extract_data(self, file_path, options, local=True, debug=False):
        markdown_text = self.invoke_pipeline_step(
            lambda: pymupdf4llm.to_markdown(file_path),
            "Extracting markdown text from the document...",
            local
        )

        content, table_content = self.invoke_pipeline_step(
            lambda: self.load_text_data(markdown_text, options),
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

    def load_text_data(self, markdown_text, options):
        content, table_content = None, None

        if options is None:
            content = markdown_text

        if options and "tables" in options and "markdown" in options:
            content = self.extract_form_data(markdown_text)
            table_content = self.extract_tables(markdown_text)

        return content, table_content

    def extract_form_data(self, markdown_text):
        return markdown_text

    def extract_tables(self, markdown_text):
        # Regular expression to match markdown tables
        table_pattern = re.compile(r'(\|.+\|\n\|[-| ]+\|\n(?:\|.*\|\n)*?)(?=\|.*TOTAL)', re.MULTILINE)

        # Find all tables in the markdown text
        tables = table_pattern.findall(markdown_text)

        html_tables = []
        for table_text in tables:
            # Split the table into lines
            lines = table_text.strip().split('\n')

            # Extract headers and rows
            headers = [self.clean_column_name(header.strip()) for header in lines[0].split('|') if header]
            rows = []
            for line in lines[2:]:  # Skip header and separator lines
                row = [cell.strip() for cell in line.split('|') if cell]
                rows.append(row)

            # Convert to Pandas DataFrame
            df = pd.DataFrame(rows, columns=headers)

            # Convert DataFrame to HTML and append to the list
            html_table = df.to_html(index=False)
            if self.table_has_header(html_table):
                html_tables.append(html_table)

            return html_tables

    def clean_column_name(self, name):
        """
        Cleans the column name by removing spaces if the name is a single word with spaces between letters.

        Args:
        name (str): The column name to clean.

        Returns:
        str: The cleaned column name.
        """
        # Check if the name contains only letters and spaces
        if all(char.isalpha() or char.isspace() for char in name):
            # Check if it is a single word with spaces between letters
            parts = name.split()
            if len(parts) > 1 and all(len(part) == 1 for part in parts):
                return ''.join(parts)
        return name

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
    processor = MarkdownProcessor()

    # content, table_content = processor.extract_data(
    #     '/Users/andrejb/infra/shared/katana-git/sparrow/sparrow-ml/llm/data/invoice_1.pdf',
    #     ['tables', 'markdown'],
    #     True,
    #     True)

