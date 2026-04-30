import importlib


class TableTemplateFactory:
    """Factory for dynamically loading and executing table template modules."""

    @staticmethod
    def get_template_module(template_name: str):
        """
        Dynamically import a table template module.

        Args:
            template_name: Name of the template (without .py extension)

        Returns:
            The imported module

        Raises:
            ImportError: If the template module cannot be found
        """
        try:
            module_path = f"pipelines.sparrow_parse.table_templates.{template_name}"
            module = importlib.import_module(module_path)
            return module
        except ImportError as e:
            raise ImportError(f"Table template '{template_name}' not found: {e}")

    @staticmethod
    def fetch_table_data(template_name: str, table_query: str, table_markdown: str) -> dict:
        """
        Load a table template module and call its fetch_table_data method.

        Args:
            template_name: Name of the template module (without .py extension)
            table_query: Query for table extraction
            table_markdown: Markdown content containing the table

        Returns:
            dict: JSON structure representing the table

        Raises:
            ImportError: If the template module cannot be found
            AttributeError: If the module doesn't have a fetch_table_data method
        """
        module = TableTemplateFactory.get_template_module(template_name)

        if not hasattr(module, 'fetch_table_data'):
            raise AttributeError(f"Module '{template_name}' does not have a 'fetch_table_data' method")

        return module.fetch_table_data(table_query, table_markdown)

    @staticmethod
    def fetch_form_data(template_name: str, rag, user_selected_pipeline: str, form_query_str: str,
                       page_file_path: str, hints_file_path: str, options_form: list, crop_size: int,
                       instruction: bool, validation: bool, ocr: bool, markdown: bool,
                       table_template: str, page_type: str, debug_dir: str, debug: bool,
                       non_tables_by_page: list, local: bool):
        """
        Load a table template module and call its fetch_form_data method.

        Args:
            template_name: Name of the template module (without .py extension)
            rag: Pipeline instance
            user_selected_pipeline: Name of the pipeline to use
            form_query_str: JSON string with form query structure
            page_file_path: Path to the document file
            hints_file_path: Path to JSON file containing query hints
            options_form: Pipeline options for form extraction
            crop_size: Crop size for extraction
            instruction: Enable instruction query
            validation: Enable validation query
            ocr: Enable data OCR enhancement
            markdown: Enable markdown output
            table_template: Table template name
            page_type: Page type query
            debug_dir: Debug folder for multipage
            debug: Enable debug mode
            non_tables_by_page: List of non-table entries by page
            local: Enable local mode for debugging

        Returns:
            Form data as dict or string

        Raises:
            ImportError: If the template module cannot be found
            AttributeError: If the module doesn't have a fetch_form_data method
        """
        module = TableTemplateFactory.get_template_module(template_name)

        if not hasattr(module, 'fetch_form_data'):
            raise AttributeError(f"Module '{template_name}' does not have a 'fetch_form_data' method")

        return module.fetch_form_data(rag, user_selected_pipeline, form_query_str, page_file_path,
                                     hints_file_path, options_form, crop_size,
                                     instruction, validation, ocr, markdown,
                                     table_template, page_type, debug_dir, debug,
                                     non_tables_by_page, local)
