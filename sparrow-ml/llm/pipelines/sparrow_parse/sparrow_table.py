import json
from rich import print
from pipelines.sparrow_parse.table_templates.table_template_factory import TableTemplateFactory
import time

def process_table_extraction(rag, user_selected_pipeline, query, file_path, hints_file_path, options, crop_size,
                            instruction, validation, ocr, markdown, table_template, page_type, debug_dir, debug):
    """
    Process document with table extraction.

    Args:
        rag: Pipeline instance
        user_selected_pipeline: Name of the pipeline to use
        query: Schema query for data extraction
        file_path: Path to the document file
        hints_file_path: Path to JSON file containing query hints
        options: Pipeline options
        crop_size: Crop size for table extraction
        instruction: Enable instruction query
        validation: Enable validation query
        ocr: Enable data ocr enhancement
        markdown: Enable markdown output
        table_template: Table template for table query
        page_type: Page type query
        debug_dir: Debug folder for multipage
        debug: Enable debug mode

    Returns:
        Extracted data as JSON string or dict
    """

    form_query, table_queries = split_query(query)

    # form_answer = None
    # if form_query:
    #     options = options[:2]
    #     form_answer = rag.run_pipeline(user_selected_pipeline, query, file_path, hints_file_path, options, crop_size,
    #                               instruction, validation, ocr, markdown, False, table_template, page_type, debug_dir,
    #                               debug, False)

    table_options = options[2:]

    ocr_query = "*"
    ocr_output = rag.run_pipeline(user_selected_pipeline, ocr_query, file_path, hints_file_path, table_options,
                                  crop_size, instruction, validation, ocr, markdown, False, table_template,
                                  page_type, debug_dir, debug, False)

    tables = extract_tables_from_ocr(ocr_output)
    if debug:
        print(f"\nExtracted tables:", tables)

    answer = {}

    # Process each table using the specified template

    if debug:
        print(f"\nTable queries: {table_queries}")

    if table_template and tables:
        for table in tables:
            # Use factory to load template and fetch table data
            try:
                table_data = TableTemplateFactory.fetch_table_data(
                    template_name=table_template,
                    table_query=table_queries,
                    table_markdown=table.get('text', '')
                )

                answer = table_data
            except (ImportError, AttributeError) as e:
                print(f"Error loading table template: {e}")

    if debug:
        print(f"\nForm query: {form_query}")

    return answer


def extract_tables_from_ocr(ocr_output):
    """
    Extract table entries from OCR output.

    Args:
        ocr_output: OCR output as a list of elements

    Returns:
        List of table entries with bbox, category, and text fields
    """
    if isinstance(ocr_output, str):
        ocr_output = json.loads(ocr_output)

    return [item for item in ocr_output if item.get('category') == 'Table']


def split_query(query):
    """
    Split query into individual parts based on form and table structures.

    Args:
        query: Schema query for data extraction

    Returns:
        Tuple of (form_query, table_queries) where:
        - form_query: Dictionary with form elements or None
        - table_queries: List of table query dictionaries
    """
    import json

    # Parse query if it's a string
    if isinstance(query, str):
        query_dict = json.loads(query)
    else:
        query_dict = query

    # Dictionary for form elements (non-array or arrays without "items" keyword)
    form_query = {}

    # Lists to store arrays with "items" in their name
    table_queries = []

    # Iterate through the query dictionary
    for key, value in query_dict.items():
        # Check if the value is a list/array and key contains "items"
        if isinstance(value, list) and "items" in key.lower():
            # Store array with "items" separately
            table_queries.append({key: value})
        else:
            # Add to form query (includes non-arrays and arrays without "items")
            form_query[key] = value

    # Return form_query as None if empty
    return (form_query if form_query else None, table_queries)