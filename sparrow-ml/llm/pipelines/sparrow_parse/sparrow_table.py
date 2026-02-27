import json
from rich import print
from pipelines.sparrow_parse.table_templates.table_template_factory import TableTemplateFactory

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

    table_options = options[2:]

    ocr_query = "*"
    ocr_output = rag.run_pipeline(user_selected_pipeline, ocr_query, file_path, hints_file_path, table_options,
                                  crop_size, instruction, validation, ocr, markdown, False, table_template,
                                  page_type, debug_dir, debug, False)

    tables, has_other_entries = extract_tables_from_ocr(ocr_output)
    if debug:
        print(f"\nExtracted tables:", tables)
        print(f"Has other entries besides tables: {has_other_entries}")
        print(f"Form query: {form_query}")
        print(f"Table queries: {table_queries}")

    answer = {}

    # Process each table using the specified template
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
        print("Table processing complete.")

    form_answer = None
    if form_query and has_other_entries:
        options = options[:2]
        form_query_str = json.dumps(form_query, ensure_ascii=False)
        form_answer = rag.run_pipeline(user_selected_pipeline, form_query_str, file_path, hints_file_path, options, crop_size,
                                  instruction, validation, ocr, markdown, False, table_template, page_type, debug_dir,
                                  debug, False)

    # Merge form_answer and answer into single JSON (form_answer values first)
    merged_result = {}

    # Parse form_answer if it exists
    if form_answer:
        if isinstance(form_answer, str):
            form_answer_dict = json.loads(form_answer)
        else:
            form_answer_dict = form_answer
        merged_result.update(form_answer_dict)

    # Parse answer if it exists
    if answer:
        if isinstance(answer, str):
            answer_dict = json.loads(answer)
        else:
            answer_dict = answer
        merged_result.update(answer_dict)

    # Format with indent=4
    final_answer = json.dumps(merged_result, indent=4, ensure_ascii=False)

    return final_answer


def extract_tables_from_ocr(ocr_output):
    """
    Extract table entries from OCR output.

    Args:
        ocr_output: OCR output as a list of elements

    Returns:
        Tuple of (tables, has_other_entries) where:
        - tables: List of table entries with bbox, category, and text fields
        - has_other_entries: Boolean indicating if OCR output contains any entries besides category Table
    """
    if isinstance(ocr_output, str):
        ocr_output = json.loads(ocr_output)

    tables = [item for item in ocr_output if item.get('category') == 'Table']
    has_other_entries = any(item.get('category') != 'Table' for item in ocr_output)

    return tables, has_other_entries


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