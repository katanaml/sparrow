from genson import SchemaBuilder
from jsonschema import validate, ValidationError
import json


class Validator:
    def __init__(self, example_json):
        self.generated_schema = self.generate_schema_from_example(example_json)

    def generate_schema_from_example(self, example_json):
        # Parse the example JSON into a Python object
        example_data = json.loads(example_json)

        # Generate the schema using Genson
        builder = SchemaBuilder()
        builder.add_object(example_data)

        return builder.to_schema()

    def validate_json_against_schema(self, json_string, schema):
        try:
            json_data = json.loads(json_string)  # Parse LLM JSON output
            validate(instance=json_data, schema=schema)  # Validate against schema
            return None  # Return None if valid
        except (json.JSONDecodeError, ValidationError) as e:
            return str(e)  # Return error message if invalid