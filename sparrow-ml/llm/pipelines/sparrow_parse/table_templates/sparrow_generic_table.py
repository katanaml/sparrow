
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
        target_type: Target type ('str', 'int', 'float', 'int or null', 'float or null', etc.)

    Returns:
        Converted value or None for nullable types with empty values
    """
    value = value.strip()

    # Check if type is nullable (e.g., 'int or null', 'float or null')
    is_nullable = 'or null' in target_type.lower()
    base_type = target_type.split()[0] if is_nullable else target_type

    # Remove common formatting characters
    cleaned_value = re.sub(r"['']", '', value)  # Remove apostrophes used as thousand separators
    cleaned_value = re.sub(r'[^\d.-]', '', cleaned_value)  # Keep only digits, dots, and minus

    # If value is empty and type is nullable, return None
    if not cleaned_value and is_nullable:
        return None

    if base_type == 'int':
        try:
            return int(float(cleaned_value)) if cleaned_value else (None if is_nullable else 0)
        except ValueError:
            return None if is_nullable else 0
    elif base_type == 'float':
        try:
            return float(cleaned_value) if cleaned_value else (None if is_nullable else 0.0)
        except ValueError:
            return None if is_nullable else 0.0
    else:  # Default to string
        return value if value else (None if is_nullable else value)


def parse_form_query(form_query_str: str) -> Dict[str, str]:
    """
    Parse the form query structure to extract field names and types.

    Args:
        form_query_str: JSON string defining form fields.
                       Example: "{'account_number': 'int', 'statement_date': 'str'}"

    Returns:
        Dictionary mapping field names to their types
    """
    if isinstance(form_query_str, str):
        form_query = json.loads(form_query_str.replace("'", '"'))
    else:
        form_query = form_query_str

    return form_query


def extract_field_value(field_name: str, non_tables_entries: List[Dict], field_type: str) -> Any:
    """
    Extract a field value from non-table entries using fuzzy matching.

    Args:
        field_name: Name of the field to extract (e.g., 'account_number')
        non_tables_entries: List of non-table entries with 'text' content
        field_type: Target type for the field ('str', 'int', 'float')

    Returns:
        Extracted value converted to the target type, or None if not found
    """
    # Normalize field name for matching (e.g., 'account_number' -> 'account number')
    normalized_field = normalize_text(field_name.replace('_', ' '))

    # Search through all text entries
    for entry in non_tables_entries:
        if 'text' not in entry:
            continue

        text = entry['text']
        lines = text.split('\n')

        for line in lines:
            # Check if this line contains a key-value pair
            if ':' in line:
                parts = line.split(':', 1)
                key = normalize_text(parts[0])
                value = parts[1].strip() if len(parts) > 1 else ''

                # Check if the key matches our field
                if key == normalized_field or normalized_field in key or key in normalized_field:
                    # Convert value to the target type
                    if field_type == 'int':
                        return convert_value(value, 'int')
                    elif field_type == 'float':
                        return convert_value(value, 'float')
                    else:
                        return value

    return None


def fetch_form_data(rag, user_selected_pipeline: str, form_query_str: str, page_file_path: str,
                    hints_file_path: str, options_form: List, crop_size: int,
                    instruction: bool, validation: bool, ocr: bool, markdown: bool,
                    table_template: str, page_type: str, debug_dir: str, debug: bool,
                    non_tables_by_page: List) -> Dict:
    """
    Extract form data from non-table entries based on query schema.

    Uses fuzzy field name matching to map query fields to text content.

    Args:
        rag: Pipeline instance (not used in this implementation)
        user_selected_pipeline: Name of the pipeline to use (not used)
        form_query_str: JSON string with form query structure
                       Example: "{'account_number': 'int', 'statement_date': 'str'}"
        page_file_path: Path to the document file (not used)
        hints_file_path: Path to JSON file containing query hints (not used)
        options_form: Pipeline options for form extraction (not used)
        crop_size: Crop size for extraction (not used)
        instruction: Enable instruction query (not used)
        validation: Enable validation query (not used)
        ocr: Enable data OCR enhancement (not used)
        markdown: Enable markdown output (not used)
        table_template: Table template name (not used)
        page_type: Page type query (not used)
        debug_dir: Debug folder for multipage (not used)
        debug: Enable debug mode (not used)
        non_tables_by_page: List of non-table entries by page

    Returns:
        Dictionary with extracted form data matching the query schema
    """

    # Not used
    # form_answer = rag.run_pipeline(user_selected_pipeline, form_query_str, page_file_path,
    #                                hints_file_path, options_form, crop_size,
    #                                instruction, validation, ocr, markdown, False, table_template,
    #                                page_type, debug_dir, debug, False)

    # Parse the form query to get field names and types
    form_fields = parse_form_query(form_query_str)

    if not form_fields or not non_tables_by_page:
        return {}

    # Collect all non-table entries from all pages
    all_non_tables = []
    for page_info in non_tables_by_page:
        if 'non_tables' in page_info:
            all_non_tables.extend(page_info['non_tables'])

    # Extract values for each field
    result = {}
    for field_name, field_type in form_fields.items():
        value = extract_field_value(field_name, all_non_tables, field_type)
        result[field_name] = value

    return result


def _parse_html_table(table_markdown: str):
    """
    Parse an HTML table string and extract the table element and its headers.

    Args:
        table_markdown: HTML string containing the table

    Returns:
        Tuple of (table_element, headers) where table_element is a BeautifulSoup
        Tag or None, and headers is a list of header strings (empty if not found)
    """
    soup = BeautifulSoup(table_markdown, 'html.parser')
    table = soup.find('table')
    if not table:
        return None, []

    headers = []
    thead = table.find('thead')
    if thead:
        header_row = thead.find('tr')
        if header_row:
            # Try <th> first, fall back to <td> if no <th> tags found
            headers = [th.get_text(strip=True) for th in header_row.find_all('th')]
            if not headers:
                headers = [td.get_text(strip=True) for td in header_row.find_all('td')]

    return table, headers


def _extract_rows(table, headers: List[str], fields: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extract data rows from a parsed table for the given field definitions.

    Args:
        table: BeautifulSoup table element
        headers: List of table header strings
        fields: List of field dicts with 'name' and 'type' keys

    Returns:
        List of row dicts with field names as keys and converted values
    """
    # Map field names to column indices
    field_to_column = {}
    for field in fields:
        column_idx = find_best_column_match(field['name'], headers)
        if column_idx is not None:
            field_to_column[field['name']] = {'index': column_idx, 'type': field['type']}

    items = []
    tbody = table.find('tbody')
    if tbody:
        for row in tbody.find_all('tr'):
            cells = row.find_all('td')
            if not cells:
                continue

            item = {}
            for field in fields:
                if field['name'] in field_to_column:
                    column_info = field_to_column[field['name']]
                    col_idx = column_info['index']
                    if col_idx < len(cells):
                        item[field['name']] = convert_value(cells[col_idx].get_text(strip=True), column_info['type'])
                    else:
                        item[field['name']] = None
                else:
                    item[field['name']] = None

            items.append(item)

    return items


def fetch_table_data(table_queries: List[str], table_markdown: str) -> dict:
    """
    Extract JSON table structure from HTML/Markdown table based on query schema.

    When table_queries is empty, all columns are identified automatically and all
    data is returned with string values (no filtering).

    When table_queries is provided, uses fuzzy column name matching to map query
    fields to table columns.

    Args:
        table_queries: List of JSON strings defining desired structure, or [] to
                      fetch all columns automatically.
                      Example: ["[{'items': [{'instrument_name': 'str', 'valuation': 'int'}]}]"]
                      Uses only the first query when provided.
        table_markdown: HTML/Markdown string containing the table

    Returns:
        dict: JSON structure with extracted data matching the query schema
    """
    table, headers = _parse_html_table(table_markdown)
    if not table or not headers:
        return {'items': []}

    if not table_queries:
        # Auto-detect: use all headers as string fields
        fields = [{'name': header, 'type': 'str'} for header in headers if header]
    else:
        fields = parse_query_structure(table_queries)
        if not fields:
            return {'items': []}

    return {'items': _extract_rows(table, headers, fields)}
