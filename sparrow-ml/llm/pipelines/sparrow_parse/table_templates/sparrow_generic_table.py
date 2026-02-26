
import json
import re
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional


def normalize_text(text: str) -> str:
    """Normalize text for comparison: lowercase, remove special chars, collapse whitespace."""
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def find_best_column_match(query_field: str, table_headers: List[str]) -> Optional[int]:
    """
    Find the best matching column index for a query field.

    Uses substring matching and similarity scoring.

    Args:
        query_field: The field name from the query (e.g., 'instrument_name')
        table_headers: List of table header names

    Returns:
        Index of the best matching column, or None if no match found
    """
    normalized_query = normalize_text(query_field)
    query_words = set(normalized_query.split())

    best_score = 0
    best_index = None

    for idx, header in enumerate(table_headers):
        normalized_header = normalize_text(header)
        header_words = set(normalized_header.split())

        # Check for exact match
        if normalized_query == normalized_header:
            return idx

        # Check for substring match
        if normalized_query in normalized_header or normalized_header in normalized_query:
            score = 0.8
        else:
            # Calculate word overlap score
            if not query_words or not header_words:
                score = 0
            else:
                common_words = query_words.intersection(header_words)
                score = len(common_words) / max(len(query_words), len(header_words))

        if score > best_score and score > 0.5:  # Threshold of 0.5
            best_score = score
            best_index = idx

    return best_index


def parse_query_structure(table_queries: List[str]) -> List[Dict[str, Any]]:
    """
    Parse the table query structure to extract field names and types.

    Args:
        table_queries: List of JSON strings, using only the first one.
                      Example: ["[{'items': [{'instrument_name': 'str', 'valuation': 'int'}]}]"]

    Returns:
        List of field definitions with name and type
    """
    if not table_queries or len(table_queries) == 0:
        return []

    # Use first query only
    table_query = table_queries[0]

    # Handle if it's already parsed
    if isinstance(table_query, str):
        query_json_str = table_query.replace("'", '"')
        query_data = json.loads(query_json_str)
    else:
        query_data = table_query

    # Extract fields from the 'items' array
    # Handle both formats: [{'items': [...]}] and {'items': [...]}
    if isinstance(query_data, dict):
        # Direct dict format
        if 'items' in query_data:
            items_schema = query_data['items']
            if isinstance(items_schema, list) and len(items_schema) > 0:
                fields = []
                for field_name, field_type in items_schema[0].items():
                    fields.append({'name': field_name, 'type': field_type})
                return fields
    elif isinstance(query_data, list) and len(query_data) > 0:
        # List wrapper format
        if 'items' in query_data[0]:
            items_schema = query_data[0]['items']
            if isinstance(items_schema, list) and len(items_schema) > 0:
                fields = []
                for field_name, field_type in items_schema[0].items():
                    fields.append({'name': field_name, 'type': field_type})
                return fields

    return []


def convert_value(value: str, target_type: str) -> Any:
    """
    Convert string value to the target type.

    Args:
        value: String value from table cell
        target_type: Target type ('str', 'int', 'float', etc.)

    Returns:
        Converted value
    """
    value = value.strip()

    # Remove common formatting characters
    cleaned_value = re.sub(r"['']", '', value)  # Remove apostrophes used as thousand separators
    cleaned_value = re.sub(r'[^\d.-]', '', cleaned_value)  # Keep only digits, dots, and minus

    if target_type == 'int':
        try:
            return int(float(cleaned_value)) if cleaned_value else 0
        except ValueError:
            return 0
    elif target_type == 'float':
        try:
            return float(cleaned_value) if cleaned_value else 0.0
        except ValueError:
            return 0.0
    else:  # Default to string
        return value


def fetch_table_data(table_queries: List[str], table_markdown: str) -> dict:
    """
    Extract JSON table structure from HTML/Markdown table based on query schema.

    Uses fuzzy column name matching to map query fields to table columns.

    Args:
        table_queries: List of JSON strings defining desired structure.
                      Example: ["[{'items': [{'instrument_name': 'str', 'valuation': 'int'}]}]"]
                      Uses only the first query.
        table_markdown: HTML/Markdown string containing the table

    Returns:
        dict: JSON structure with extracted data matching the query schema
    """
    # Parse the query structure
    fields = parse_query_structure(table_queries)
    if not fields:
        return {'items': []}

    # Parse the HTML table
    soup = BeautifulSoup(table_markdown, 'html.parser')
    table = soup.find('table')

    if not table:
        return {'items': []}

    # Extract headers
    headers = []
    thead = table.find('thead')
    if thead:
        header_row = thead.find('tr')
        if header_row:
            # Try <th> first, fall back to <td> if no <th> tags found
            headers = [th.get_text(strip=True) for th in header_row.find_all('th')]
            if not headers:
                headers = [td.get_text(strip=True) for td in header_row.find_all('td')]

    if not headers:
        return {'items': []}

    # Map query fields to column indices
    field_to_column = {}
    for field in fields:
        column_idx = find_best_column_match(field['name'], headers)
        if column_idx is not None:
            field_to_column[field['name']] = {'index': column_idx, 'type': field['type']}

    # Extract data rows
    items = []
    tbody = table.find('tbody')
    if tbody:
        rows = tbody.find_all('tr')
        for row in rows:
            cells = row.find_all('td')
            if len(cells) == 0:
                continue

            item = {}
            for field in fields:
                if field['name'] in field_to_column:
                    column_info = field_to_column[field['name']]
                    column_idx = column_info['index']
                    if column_idx < len(cells):
                        cell_value = cells[column_idx].get_text(strip=True)
                        item[field['name']] = convert_value(cell_value, column_info['type'])
                    else:
                        item[field['name']] = None
                else:
                    item[field['name']] = None

            items.append(item)

    return {'items': items}
