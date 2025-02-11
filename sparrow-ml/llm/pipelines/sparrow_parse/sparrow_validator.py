import json
from genson import SchemaBuilder
from jsonschema import validate, ValidationError


class JSONValidator:
    """
    A utility class to generate JSON schemas from examples and validate JSON strings against them.
    Supports types: int, str, float, int or null, str or null, float or null
    """
    TYPE_MAPPING = {
        'int': {'type': 'integer'},
        'str': {'type': 'string'},
        'float': {'type': 'number'},
        'int or null': {'type': ['integer', 'null']},
        'str or null': {'type': ['string', 'null']},
        'float or null': {'type': ['number', 'null']}
    }

    def __init__(self, example_json: str):
        """
        Initializes the validator by generating a schema from the provided example JSON.
        """
        self.generated_schema = self._generate_schema_from_example(example_json)

    @staticmethod
    def _get_type_definition(field_value: str) -> dict:
        """
        Determines the JSON schema type definition based on the field value.

        Args:
            field_value (str): The type specification string (e.g., 'str', 'int or null')

        Returns:
            dict: The corresponding JSON schema type definition

        Raises:
            ValueError: If an unsupported type is provided
        """
        field_value = field_value.lower().strip()
        if field_value not in JSONValidator.TYPE_MAPPING:
            raise ValueError(f"Unsupported type: {field_value}. Supported types are: "
                             f"{', '.join(JSONValidator.TYPE_MAPPING.keys())}")

        return JSONValidator.TYPE_MAPPING[field_value]


    @staticmethod
    def _generate_schema_from_example(example_json: str) -> dict:
        """
        Generates a JSON schema from an example JSON string.

        Args:
            example_json (str): A JSON string representing an example with type specifications.

        Returns:
            dict: A JSON schema generated from the example.

        Raises:
            ValueError: If the example JSON is invalid or contains unsupported types
        """
        try:
            example_data = json.loads(example_json)

            schema = {
                "$schema": "http://json-schema.org/schema#",
                "type": "object",
                "properties": {},
                "required": []
            }

            for field_name, field_value in example_data.items():
                if not isinstance(field_value, str):
                    raise ValueError(f"Field '{field_name}' value must be a type specification string")

                try:
                    type_definition = JSONValidator._get_type_definition(field_value)
                    schema["properties"][field_name] = type_definition
                    schema["required"].append(field_name)
                except ValueError as e:
                    raise ValueError(f"Invalid type for field '{field_name}': {str(e)}")

            return schema

        except json.JSONDecodeError as e:
            raise ValueError("Invalid example JSON provided.") from e


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