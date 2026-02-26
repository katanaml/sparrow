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
