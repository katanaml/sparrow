import json
from jsonschema import validate, ValidationError


class JSONValidator:
    """
    A utility class to generate JSON schemas from examples and validate JSON strings against them.
    Supports types: int, str, float, int or null, str or null, float or null
    Also supports direct numeric values (int/float) in schema specification
    """
    TYPE_MAPPING = {
        'int': {'type': 'integer'},
        'str': {'type': 'string'},
        'float': {'type': 'number'},
        'int or null': {'type': ['integer', 'null']},
        'str or null': {'type': ['string', 'null']},
        'float or null': {'type': ['number', 'null']},
        '0 or null': {
            'anyOf': [
                {'type': 'integer'},
                {'type': 'number'},
                {'type': 'string', 'pattern': '^[0-9]+(\.[0-9]+)?$'},
                {'type': 'null'}
            ]
        }
    }

    def __init__(self, example_json: str):
        """
        Initializes the validator by generating a schema from the provided example JSON.
        """
        self.generated_schema = self._generate_schema_from_example(example_json)

    @staticmethod
    def _get_type_definition(field_value: str | int | float) -> dict:
        """
        Determines the JSON schema type definition based on the field value.

        Args:
            field_value: Type specification string or direct numeric value

        Returns:
            dict: The corresponding JSON schema type definition
        """
        if isinstance(field_value, int):
            return {'type': 'integer'}
        if isinstance(field_value, float):
            return {'type': 'number'}

        field_value = str(field_value).lower().strip()
        if field_value not in JSONValidator.TYPE_MAPPING:
            raise ValueError(f"Unsupported type: {field_value}. Supported types are: "
                             f"{', '.join(JSONValidator.TYPE_MAPPING.keys())}")

        return JSONValidator.TYPE_MAPPING[field_value]

    @staticmethod
    def _generate_schema_from_example(example_json: str) -> dict:
        """
        Generates a JSON schema from an example JSON string.
        Handles both single objects and arrays of objects.
        """
        try:
            example_data = json.loads(example_json)

            # If the example is an array, use the first object as the template
            if isinstance(example_data, list):
                if not example_data:
                    raise ValueError("Empty array provided as example")
                example_data = example_data[0]

            if not isinstance(example_data, dict):
                raise ValueError("Example must be either a JSON object or an array of objects")

            schema = {
                "$schema": "http://json-schema.org/schema#",
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }

            for field_name, field_value in example_data.items():
                # Handle both string type specifications and direct numeric values
                if not (isinstance(field_value, (str, int, float))):
                    raise ValueError(f"Field '{field_name}' value must be a type specification string or numeric value")

                try:
                    type_definition = JSONValidator._get_type_definition(field_value)
                    schema["items"]["properties"][field_name] = type_definition
                    schema["items"]["required"].append(field_name)
                except ValueError as e:
                    raise ValueError(f"Invalid type for field '{field_name}': {str(e)}")

            return schema

        except json.JSONDecodeError as e:
            raise ValueError("Invalid example JSON provided.") from e

    @staticmethod
    def validate_json_against_schema(json_string: str, schema: dict) -> str:
        """
        Validates a JSON string against a given schema.
        """
        try:
            json_data = json.loads(json_string)
            # If input is a single object, wrap it in an array
            if isinstance(json_data, dict):
                json_data = [json_data]
            validate(instance=json_data, schema=schema)
            return None  # Validation succeeded
        except json.JSONDecodeError:
            return "Invalid JSON format. Could not parse the input JSON."
        except ValidationError as e:
            return f"Schema validation error: {e.message}"