import json
from rich import print
from pipelines.sparrow_parse.table_templates.table_template_factory import TableTemplateFactory
import os
from pypdf import PdfReader, PdfWriter
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
    start_time = time.time()

    form_query, table_queries = split_query(query)

    table_options = options[2:]

    ocr_query = "*"
    ocr_output = rag.run_pipeline(user_selected_pipeline, ocr_query, file_path, hints_file_path, table_options,
                                  crop_size, instruction, validation, ocr, markdown, False, table_template,
                                  page_type, debug_dir, debug, False)

    tables_by_page = extract_tables_from_ocr(ocr_output)
    if debug:
        print(f"\nExtracted tables by page:", tables_by_page)
        print(f"Form query: {form_query}")
        print(f"Table queries: {table_queries}")

    all_pages_data = []

    # Check if we need to split PDF for multi-page processing with forms
    split_files = []
    is_multipage = len(tables_by_page) > 1

    if is_multipage and file_path.lower().endswith('.pdf'):
        # Split PDF into separate pages
        split_files = split_pdf_by_pages(file_path, tables_by_page)

    # Process tables from each page using the specified template
    if table_template and tables_by_page:
        for idx, page_info in enumerate(tables_by_page):
            page_number = page_info['page']
            tables = page_info['tables']
            has_other_entries = page_info['has_other_entries']

            # Process form data if page has other entries
            form_answer = None
            if form_query and has_other_entries:
                options_form = options[:2]
                form_query_str = json.dumps(form_query, ensure_ascii=False)
                # Use split file for multipage, original file for single page
                page_file_path = split_files[idx] if is_multipage and split_files else file_path

                if debug:
                    print(f"Processing form data for page {page_number} from {page_file_path}")

                form_answer = rag.run_pipeline(user_selected_pipeline, form_query_str, page_file_path,
                                             hints_file_path, options_form, crop_size,
                                             instruction, validation, ocr, markdown, False, table_template,
                                             page_type, debug_dir, debug, False)

            if debug:
                print(f"\nProcessing page {page_number} with {len(tables)} table(s)")

            for table in tables:
                # Use factory to load template and fetch table data
                try:
                    table_data = TableTemplateFactory.fetch_table_data(
                        template_name=table_template,
                        table_query=table_queries,
                        table_markdown=table.get('text', '')
                    )

                    # Merge form_answer with table_data if form data exists
                    merged_data = {}
                    if form_answer:
                        # Parse form_answer if it's a string
                        if isinstance(form_answer, str):
                            form_answer_dict = json.loads(form_answer)
                        else:
                            form_answer_dict = form_answer
                        merged_data.update(form_answer_dict)

                    # Add table data
                    merged_data.update(table_data)

                    # Add page with data structure similar to OCR output
                    all_pages_data.append({
                        'data': merged_data,
                        'page': page_number
                    })

                except (ImportError, AttributeError) as e:
                    print(f"Error loading table template for page {page_number}: {e}")
                break  # Process only the first table from each page for now

    # Simplify structure for single page - return just the data without page wrapper
    if len(all_pages_data) == 1:
        answer = all_pages_data[0]['data']
    else:
        answer = all_pages_data

    # Cleanup split PDF files
    if split_files:
        cleanup_split_files(split_files)

    end_time = time.time()
    print(f"\nTotal time with table processing: {end_time - start_time:.2f} seconds")

    return json.dumps(answer, indent=4, ensure_ascii=False)


def extract_tables_from_ocr(ocr_output):
    """
    Extract table entries from OCR output, handling both single-page and multi-page structures.

    Args:
        ocr_output: OCR output as a list of elements (single page) or list of page objects (multi-page)
                   Multi-page format: [{"page": 1, "data": [...]}, {"page": 2, "data": [...]}]

    Returns:
        List of dicts with 'page', 'tables', and 'has_other_entries' keys per page
        e.g. [{'page': 1, 'tables': [...], 'has_other_entries': True}, ...]
    """
    if isinstance(ocr_output, str):
        ocr_output = json.loads(ocr_output)

    tables_by_page = []

    # Check if this is multi-page format (list of objects with 'page' and 'data' keys)
    if isinstance(ocr_output, list) and len(ocr_output) > 0 and isinstance(ocr_output[0], dict) and 'page' in ocr_output[0]:
        # Multi-page format
        for page_obj in ocr_output:
            page_number = page_obj.get('page', 0)
            page_data = page_obj.get('data', [])

            # Extract tables from this page
            tables = [item for item in page_data if item.get('category') == 'Table']

            # Check if this page has other entries
            page_has_other_entries = any(item.get('category') != 'Table' for item in page_data)

            if tables:
                tables_by_page.append({
                    'page': page_number,
                    'tables': tables,
                    'has_other_entries': page_has_other_entries
                })
    else:
        # Single page format (backward compatibility)
        tables = [item for item in ocr_output if item.get('category') == 'Table']
        has_other_entries = any(item.get('category') != 'Table' for item in ocr_output)

        if tables:
            tables_by_page.append({
                'page': 1,
                'tables': tables,
                'has_other_entries': has_other_entries
            })

    return tables_by_page


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


def split_pdf_by_pages(pdf_path, tables_by_page):
    """
    Split a multi-page PDF into separate single-page PDF files.

    Args:
        pdf_path: Path to the source PDF file
        tables_by_page: List of page info dicts with 'page' keys

    Returns:
        List of paths to the split PDF files
    """
    split_files = []

    try:
        reader = PdfReader(pdf_path)
        base_name = os.path.splitext(pdf_path)[0]

        for page_info in tables_by_page:
            page_number = page_info['page']
            # Page numbers are 1-based, but PyPDF2 uses 0-based indexing
            page_index = page_number - 1

            if page_index < len(reader.pages):
                writer = PdfWriter()
                writer.add_page(reader.pages[page_index])

                split_file_path = f"{base_name}_page_{page_number}.pdf"
                with open(split_file_path, 'wb') as output_file:
                    writer.write(output_file)

                split_files.append(split_file_path)
    except Exception as e:
        print(f"Error splitting PDF: {e}")
        # Clean up any files that were created before the error
        cleanup_split_files(split_files)
        return []

    return split_files


def cleanup_split_files(split_files):
    """
    Remove temporary split PDF files.

    Args:
        split_files: List of file paths to remove
    """
    import os

    for file_path in split_files:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Error removing temporary file {file_path}: {e}")