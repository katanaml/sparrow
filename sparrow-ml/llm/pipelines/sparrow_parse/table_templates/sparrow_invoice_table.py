from typing import List, Dict, Any


def fetch_form_data(rag, user_selected_pipeline: str, form_query_str: str, page_file_path: str,
                    hints_file_path: str, options_form: List, crop_size: int,
                    instruction: bool, validation: bool, ocr: bool, markdown: bool,
                    table_template: str, page_type: str, debug_dir: str, debug: bool,
                    non_tables_by_page: List, local: bool) -> Dict:
    """
    Extract invoice form data from non-table entries based on query schema.

    Args:
        rag: Pipeline instance (not used in this implementation)
        user_selected_pipeline: Name of the pipeline to use (not used)
        form_query_str: JSON string with form query structure
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
        local: Enable local mode for debugging

    Returns:
        Dictionary with extracted form data matching the query schema
    """
    # TODO: Implement invoice-specific form data extraction from non-table entries
    # Expected to extract fields like: invoice_number, invoice_date, due_date, vendor_name, etc.
    return {}


def fetch_table_data(table_query: str, table_markdown: str) -> dict:
    """
    Extract invoice line items table structure from Markdown.

    Args:
        table_query: Query schema for table extraction
        table_markdown: Markdown content containing the invoice table

    Returns:
        dict: JSON structure representing the invoice table with line items
    """
    # TODO: Implement invoice-specific table structure extraction from Markdown
    # Expected to extract columns like: item_description, quantity, unit_price, total
    return {}
