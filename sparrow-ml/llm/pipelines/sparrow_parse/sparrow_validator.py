import json
from genson import SchemaBuilder
from jsonschema import validate, ValidationError


class JSONValidator:
    """
    A utility class to generate JSON schemas from examples and validate JSON strings against them.
    """
    def __init__(self, example_json: str):
        """
        Initializes the validator by generating a schema from the provided example JSON.
        """
        self.generated_schema = self._generate_schema_from_example(example_json)

    @staticmethod
    def _generate_schema_from_example(example_json: str) -> dict:
        """
        Generates a JSON schema from an example JSON string.

        Args:
            example_json (str): A JSON string representing an example.

        Returns:
            dict: A JSON schema generated from the example.
        """
        try:
            # Parse the example JSON into a Python dictionary
            example_data = json.loads(example_json)
        except json.JSONDecodeError as e:
            raise ValueError("Invalid example JSON provided.") from e

        # Use Genson to build the schema
        builder = SchemaBuilder()
        builder.add_object(example_data)
        return builder.to_schema()

    @staticmethod
    def validate_json_against_schema(json_string: str, schema: dict) -> str:
        """
        Validates a JSON string against a given schema.

        Args:
            json_string (str): The JSON string to validate.
            schema (dict): The JSON schema to validate against.

        Returns:
            str: An error message if validation fails, or None if the validation succeeds.
        """
        try:
            # Parse the JSON string into a dictionary
            json_data = json.loads(json_string)
            validate(instance=json_data, schema=schema)
            return None  # Validation succeeded
        except json.JSONDecodeError:
            return "Invalid JSON format. Could not parse the input JSON."
        except ValidationError as e:
            return f"Schema validation error: {e.message}"