from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer, util
import pandas as pd
import re
from io import StringIO


def merge_html_table_headers(html_table, column_keywords, debug=False):
    soup = BeautifulSoup(html_table, 'html.parser')

    # Find all thead elements
    theads = soup.find_all('thead')

    if len(theads) > 1 and column_keywords is not None:
        html_table = update_table_header_colspan(html_table)
        html_table = merge_table_header_thead(html_table)
        html_table = merge_colspan_columns(html_table)
        html_table = normalize_html_table(html_table, debug)
        html_table = fix_rowspan_elements(html_table)
        html_table = merge_rows_with_rowspan(html_table)
        html_table = detect_and_remove_junk_columns(html_table, column_keywords, debug)
    else:
        # If there is only one thead, return the original table
        return html_table

    return html_table


def update_table_header_colspan(html_table):
    soup = BeautifulSoup(html_table, 'html.parser')
    theads = soup.find_all('thead')

    for thead in theads:
        for th in thead.find_all('th'):
            colspan = th.get('colspan')
            if colspan and int(colspan) > 1:
                colspan_count = int(colspan)
                th['colspan'] = 1
                for _ in range(colspan_count - 1):
                    new_th = soup.new_tag('th')
                    th.insert_after(new_th)

    return str(soup)


def merge_table_header_thead(html_table):
    soup = BeautifulSoup(html_table, 'html.parser')
    theads = soup.find_all('thead')

    primary_thead = theads[0]
    secondary_thead = theads[1]

    primary_ths = primary_thead.find_all('th')
    secondary_ths = secondary_thead.find_all('th')

    for i, th in enumerate(primary_ths):
        if i < len(secondary_ths):
            primary_text = th.text.strip()
            secondary_text = secondary_ths[i].text.strip()
            if primary_text and secondary_text:
                th.string = (primary_text + ' ' + secondary_text).strip()
            elif not primary_text and secondary_text:
                th.string = secondary_text
        # Remove colspan and rowspan attributes
        th.attrs.pop('colspan', None)
        th.attrs.pop('rowspan', None)

    secondary_thead.decompose()

    return str(soup)


def merge_colspan_columns(html_table):
    # Parse the HTML
    soup = BeautifulSoup(html_table, 'html.parser')

    # Process colspan attributes by adding empty <td> elements
    for row in soup.find_all('tr'):
        cols = []
        for cell in row.find_all(['th', 'td']):
            colspan = int(cell.get('colspan', 1))
            # Add the cell and additional empty cells if colspan is greater than 1
            cols.append(cell)
            for _ in range(colspan - 1):
                new_td = soup.new_tag('td')
                cols.append(new_td)
            # Remove the colspan attribute
            if cell.has_attr('colspan'):
                del cell['colspan']

        # Replace the row's children with the updated cells
        row.clear()
        row.extend(cols)

    return str(soup)


def normalize_html_table(html, debug = False):
    soup = BeautifulSoup(html, 'html.parser')

    # Find the header row and count the number of cells
    header = soup.find('thead').find_all(['th', 'td'])
    header_cell_count = len(header)

    if debug:
        # Print the number of header cells
        print(f"Number of cells in header: {header_cell_count}")

    # Find all rows in the table body
    rows = soup.find_all('tr')

    for row in rows:
        cells = row.find_all(['td', 'th'])
        if len(cells) > header_cell_count:
            extra_cells = len(cells) - header_cell_count
            for cell in cells:
                if cell.text.strip() == '' and extra_cells > 0:
                    cell.decompose()
                    extra_cells -= 1
        elif len(cells) < header_cell_count:
            missing_cells = header_cell_count - len(cells)
            for _ in range(missing_cells):
                new_cell = soup.new_tag('td')
                row.insert(0, new_cell)

    return str(soup)


def fix_rowspan_elements(html_table):
    # Parse the HTML table
    soup = BeautifulSoup(html_table, 'html.parser')

    # Find all table rows
    rows = soup.find_all('tr')

    # Dictionary to store rows with rowspan elements
    rowspan_dict = {}

    # Iterate over each row
    for row_index, row in enumerate(rows):
        # Find all cells in the row
        cells = row.find_all(['td', 'th'])

        # Iterate over each cell
        for cell_index, cell in enumerate(cells):
            # Check if the cell has a rowspan attribute
            if cell.has_attr('rowspan'):
                # Store the rowspan value and cell position
                rowspan_value = int(cell['rowspan'])
                if row_index not in rowspan_dict:
                    rowspan_dict[row_index] = []
                rowspan_dict[row_index].append((cell_index, rowspan_value))

    # List to store the number of rows until the next rowspan row
    rows_below_until_next_rowspan = []

    # Get the sorted row indices that have rowspan elements
    sorted_row_indices = sorted(rowspan_dict.keys())

    # Calculate rows below each rowspan row until the next rowspan row
    for i in range(len(sorted_row_indices)):
        current_row = sorted_row_indices[i]
        if i < len(sorted_row_indices) - 1:
            next_row = sorted_row_indices[i + 1]
            rows_below = next_row - current_row - 1
        else:
            rows_below = len(rows) - current_row - 1
        rows_below_until_next_rowspan.append((current_row, rows_below))

    # Detect rows where rowspan value is incorrect
    rows_with_bad_rowspan = []
    for row_index, rows_below in rows_below_until_next_rowspan:
        if row_index in rowspan_dict:
            for cell_index, rowspan_value in rowspan_dict[row_index]:
                if rowspan_value - 1 < rows_below:
                    print(f"Row {row_index} has a large rowspan value: {rowspan_value}")
                    rows_with_bad_rowspan.append(row_index)
                    break

    # Modify the HTML table to adjust the rowspan attributes
    for row_index in rows_with_bad_rowspan:
        if row_index in rowspan_dict:
            for cell_index, rowspan_value in rowspan_dict[row_index]:
                # Find the cell with the rowspan attribute
                cell = rows[row_index].find_all(['td', 'th'])[cell_index]
                # Remove the rowspan attribute
                del cell['rowspan']
                # Find the next row and assign the rowspan value
                next_row_index = row_index + 1
                if next_row_index < len(rows):
                    next_row_cells = rows[next_row_index].find_all(['td', 'th'])
                    if len(next_row_cells) > cell_index:
                        next_row_cell = next_row_cells[cell_index]
                        next_row_cell['rowspan'] = rowspan_value
                    else:
                        # Create a new cell if it does not exist
                        new_cell = soup.new_tag(cell.name)
                        new_cell['rowspan'] = rowspan_value
                        new_cell.string = cell.string
                        rows[next_row_index].append(new_cell)

    # Return the modified HTML table
    return str(soup)


def merge_rows_with_rowspan(html):
    # Parse the HTML table using BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')

    # Extract the header
    thead = soup.find('thead')

    # Find all rows
    rows = soup.find_all('tr')

    result = []
    i = 0

    while i < len(rows):
        row = rows[i]
        # Check if any td in the row has a rowspan attribute
        for td in row.find_all('td'):
            if td.has_attr('rowspan'):
                rowspan_value = int(td['rowspan'])
                result.append(row)

                skip_concatenation = False
                concatenation_pairs = []

                # Add rows below the current row based on the rowspan number
                for j in range(1, rowspan_value):
                    if i + j < len(rows):
                        below_row = rows[i + j]

                        # Compare cells
                        row_cells = row.find_all('td')
                        below_row_cells = below_row.find_all('td')
                        min_length = min(len(row_cells), len(below_row_cells))

                        for k in range(min_length):
                            if is_numeric(row_cells[k].get_text(strip=True)) and is_numeric(below_row_cells[k].get_text(strip=True)):
                                skip_concatenation = True
                                break
                            else:
                                concatenation_pairs.append((row_cells[k], below_row_cells[k]))

                        if skip_concatenation:
                            result.append(below_row)

                if not skip_concatenation:
                    for row_cell, below_row_cell in concatenation_pairs:
                        concatenated_text = (row_cell.get_text(strip=True) + ' ' + below_row_cell.get_text(strip=True)).strip()
                        row_cell.string = concatenated_text

                i += rowspan_value - 1  # Skip the rows that have been added
                break
            else:
                result.append(row)
                break
        i += 1

    # Convert result list of rows back to an HTML table string
    new_table_soup = BeautifulSoup(f'<table>{str(thead)}</table>', 'html.parser')
    tbody = new_table_soup.new_tag('tbody')
    new_table_soup.table.append(tbody)
    for row in result:
        for td in row.find_all('td'):
            if td.has_attr('rowspan'):
                del td['rowspan']
        tbody.append(row)

    return str(new_table_soup.table)


def detect_and_remove_junk_columns(html_table, target_columns, debug=False):
    html_table = clean_html_table_header_names(html_table)

    # Wrap the HTML string in a StringIO object
    html_buffer = StringIO(html_table)

    # Read the HTML table
    df = pd.read_html(html_buffer)[0]

    model = SentenceTransformer('all-mpnet-base-v2')

    # Get the column names of the dataframe
    column_names = df.columns.tolist()

    # Calculate the similarity of each column name to the target column names
    target_embeddings = model.encode(target_columns)
    column_embeddings = model.encode(column_names)

    # Initialize a dictionary to store the similarity scores
    similarity_scores = {}

    # Identify junk columns based on similarity threshold
    junk_columns = []
    similarity_threshold = 0.5  # Adjust this threshold as needed

    for idx, col_embedding in enumerate(column_embeddings):
        similarities = util.pytorch_cos_sim(col_embedding, target_embeddings)[0]
        max_similarity = max(similarities)
        max_similarity_idx = similarities.argmax().item()  # Get the index of the max similarity
        similarity_scores[column_names[idx]] = (
        max_similarity.item(), target_columns[max_similarity_idx])  # Store similarity score and target column name
        if max_similarity < similarity_threshold:
            junk_columns.append(column_names[idx])

    if debug:
        # Print the similarity scores for debugging purposes
        for column, (score, target_col) in similarity_scores.items():
            print(f"Column: {column}, Similarity: {score:.4f}, Target Column: {target_col}")

    # Handle junk columns by concatenating their values to the nearest column on the left
    for junk_col in junk_columns:
        junk_col_index = column_names.index(junk_col)
        if junk_col_index > 0:
            nearest_col = column_names[junk_col_index - 1]
            df[nearest_col] = df.apply(
                lambda row: str(row[junk_col]) if pd.isna(row[nearest_col]) and pd.notna(row[junk_col])
                else (str(row[nearest_col]) + ' ' + str(row[junk_col])) if pd.notna(row[junk_col])
                else row[nearest_col],
                axis=1
            )
        df.drop(columns=[junk_col], inplace=True)

    # Replace any remaining NaN values with empty strings
    df = df.fillna('')

    if debug:
        print(f"Junk columns: {junk_columns}")
        print(df.to_string())

    # Convert the result into an HTML table
    html_table = df.to_html(index=False)

    if debug:
        print(html_table)

    return html_table


def clean_html_table_header_names(html_table: str) -> str:
    """
        Cleans the headers of an HTML table by removing junk characters and returns the updated HTML as a string.

        Parameters:
        html (str): The HTML content containing the table.

        Returns:
        str: The updated HTML table with cleaned headers.
        """
    # Parse the HTML table
    soup = BeautifulSoup(html_table, "html.parser")
    table = soup.find("table")

    # Extract the headers and clean them
    headers = table.find_all("th")
    for th in headers:
        clean_header = re.sub(r"[^a-zA-Z0-9\s]", "", th.get_text())
        # Check if the cleaned name is empty
        if not clean_header.strip():
            clean_header = "-"
        th.string.replace_with(clean_header)

    html_table = str(soup)

    return html_table


def is_numeric(value):
    # Check if the value is numeric
    return bool(re.match(r'^\d+(?:,\d{3})*(?:\.\d+)?$', value))
