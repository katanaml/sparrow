import json
from jsonschema import validate, ValidationError


class JSONValidator:
    """
    A utility class to generate JSON schemas from examples and validate JSON strings against them.
    Supports types: int, str, float, int or null, str or null, float or null
    Also supports nested arrays of objects
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
                {'type': 'string', 'pattern': r'^[0-9]+(\.[0-9]+)?$'},
                {'type': 'null'}
            ]
        },
        '0.0 or null': {
            'anyOf': [
                {'type': 'number'},
                {'type': 'string', 'pattern': r'^[0-9]+(\.[0-9]+)?$'},
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
        """
        if isinstance(field_value, int):
            return {'type': 'integer'}
        if isinstance(field_value, float):
            return {'type': 'number'}

        field_value = str(field_value).lower().strip()

        # Handle numeric variants
        if field_value.endswith(' or null'):
            numeric_part = field_value.replace(' or null', '')
            try:
                float(numeric_part)  # Check if it's a valid number
                return {
                    'anyOf': [
                        {'type': 'number'},
                        {'type': 'string', 'pattern': r'^[0-9]+(\.[0-9]+)?$'},
                        {'type': 'null'}
                    ]
                }
            except ValueError:
                pass  # Not a numeric variant, continue with normal processing

        if field_value not in JSONValidator.TYPE_MAPPING:
            raise ValueError(f"Unsupported type: {field_value}. Supported types are: "
                             f"{', '.join(JSONValidator.TYPE_MAPPING.keys())}")

        return JSONValidator.TYPE_MAPPING[field_value]

    @staticmethod
    def _process_schema_item(item_value):
        """
        Process a schema item which can be a simple type or a nested object/array.
        """
        if isinstance(item_value, list) and len(item_value) > 0:
            # Handle array of objects
            if isinstance(item_value[0], dict):
                nested_properties = {}
                nested_required = []

                for prop_name, prop_value in item_value[0].items():
                    if isinstance(prop_value, dict):
                        # Handle nested object
                        nested_obj_props, nested_obj_req = JSONValidator._process_nested_object(prop_value)
                        nested_properties[prop_name] = {
                            'type': 'object',
                            'properties': nested_obj_props,
                            'required': nested_obj_req
                        }
                    elif isinstance(prop_value, list):
                        # Handle nested array
                        nested_properties[prop_name] = JSONValidator._process_schema_item(prop_value)
                    else:
                        # Handle simple type
                        nested_properties[prop_name] = JSONValidator._get_type_definition(prop_value)

                    nested_required.append(prop_name)

                return {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': nested_properties,
                        'required': nested_required
                    }
                }
            else:
                # Simple array of values
                return {
                    'type': 'array',
                    'items': JSONValidator._get_type_definition(item_value[0])
                }
        else:
            return JSONValidator._get_type_definition(item_value)

    @staticmethod
    def _process_nested_object(obj_value):
        """
        Process a nested object in the schema.
        """
        properties = {}
        required = []

        for field_name, field_value in obj_value.items():
            if isinstance(field_value, dict):
                # Handle nested object
                nested_props, nested_req = JSONValidator._process_nested_object(field_value)
                properties[field_name] = {
                    'type': 'object',
                    'properties': nested_props,
                    'required': nested_req
                }
            elif isinstance(field_value, list):
                # Handle array
                properties[field_name] = JSONValidator._process_schema_item(field_value)
            else:
                # Handle simple type
                properties[field_name] = JSONValidator._get_type_definition(field_value)

            required.append(field_name)

        return properties, required

    @staticmethod
    def _generate_schema_from_example(example_json: str) -> dict:
        """
        Generates a JSON schema from an example JSON string.
        Handles both single objects and arrays of objects, including nested structures.
        """
        try:
            example_data = json.loads(example_json)

            # If the example is an array, use the first object as the template
            is_array = isinstance(example_data, list)
            if is_array:
                if not example_data:
                    raise ValueError("Empty array provided as example")
                example_data = example_data[0]

            if not isinstance(example_data, dict):
                raise ValueError("Example must be either a JSON object or an array of objects")

            schema = {
                "$schema": "http://json-schema.org/schema#",
                "type": "object" if not is_array else "array",
                "properties": {},
                "required": []
            }

            if is_array:
                schema["items"] = {
                    "type": "object",
                    "properties": {},
                    "required": []
                }

            # Determine where to add properties based on whether it's an array or object
            properties_target = schema["items"]["properties"] if is_array else schema["properties"]
            required_target = schema["items"]["required"] if is_array else schema["required"]

            for field_name, field_value in example_data.items():
                if isinstance(field_value, dict):
                    # Handle nested object
                    nested_props, nested_req = JSONValidator._process_nested_object(field_value)
                    properties_target[field_name] = {
                        'type': 'object',
                        'properties': nested_props,
                        'required': nested_req
                    }
                elif isinstance(field_value, list):
                    # Handle array
                    properties_target[field_name] = JSONValidator._process_schema_item(field_value)
                elif isinstance(field_value, (str, int, float)):
                    # Handle simple type
                    properties_target[field_name] = JSONValidator._get_type_definition(field_value)
                else:
                    raise ValueError(f"Field '{field_name}' has unsupported value type: {type(field_value)}")

                required_target.append(field_name)

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

            # Handle the case where schema expects array but input is object or vice versa
            schema_expects_array = schema.get("type") == "array"
            data_is_array = isinstance(json_data, list)

            if schema_expects_array and not data_is_array:
                json_data = [json_data]  # Wrap object in array
            elif not schema_expects_array and data_is_array:
                if len(json_data) > 0:
                    json_data = json_data[0]  # Unwrap array to get first object
                else:
                    json_data = {}  # Empty array becomes empty object

            validate(instance=json_data, schema=schema)
            return None  # Validation succeeded
        except json.JSONDecodeError:
            return "Invalid JSON format. Could not parse the input JSON."
        except ValidationError as e:
            return f"Schema validation error: {e.message}"