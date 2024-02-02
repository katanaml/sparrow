from rag.plugins.interface import Pipeline as PipelineInterface
from typing import Any
from pydantic import BaseModel
import json
import pydantic
from pydantic import ValidationError
from typing import Optional, List
from colorama import Fore
from haystack import component
from haystack.components.builders import PromptBuilder
from haystack_integrations.components.generators.ollama import OllamaGenerator
from haystack import Pipeline


class HaystackPipeline(PipelineInterface):
    def run_pipeline(self,
                     payload: str,
                     query_inputs: [str],
                     query_types: [str],
                     query: str,
                     debug: bool = False,
                     local: bool = True) -> Any:
        print(f"\nRunning pipeline with {payload}\n")

        class City(BaseModel):
            name: str
            country: str
            population: int

        class CitiesData(BaseModel):
            cities: List[City]

        json_schema = CitiesData.schema_json(indent=2)

        # Define the component input parameters
        @component
        class OutputValidator:
            def __init__(self, pydantic_model: pydantic.BaseModel):
                self.pydantic_model = pydantic_model
                self.iteration_counter = 0

            # Define the component output
            @component.output_types(valid_replies=List[str], invalid_replies=Optional[List[str]],
                                    error_message=Optional[str])
            def run(self, replies: List[str]):

                self.iteration_counter += 1

                ## Try to parse the LLM's reply ##
                # If the LLM's reply is a valid object, return `"valid_replies"`
                try:
                    output_dict = json.loads(replies[0])
                    self.pydantic_model.model_validate(output_dict)
                    print(
                        Fore.GREEN
                        + f"OutputValidator at Iteration {self.iteration_counter}: Valid JSON from LLM - No need for looping: {replies[0]}"
                    )
                    return {"valid_replies": replies}

                # If the LLM's reply is corrupted or not valid, return "invalid_replies" and the "error_message" for LLM to try again
                except (ValueError, ValidationError) as e:
                    print(
                        Fore.RED
                        + f"OutputValidator at Iteration {self.iteration_counter}: Invalid JSON from LLM - Let's try again.\n"
                          f"Output from LLM:\n {replies[0]} \n"
                          f"Error from OutputValidator: {e}"
                    )
                    return {"invalid_replies": replies, "error_message": str(e)}

        output_validator = OutputValidator(pydantic_model=CitiesData)

        prompt_template = """
        Create a JSON object from the information present in this passage: {{passage}}.
        Only use information that is present in the passage. Follow this JSON schema, but only return the actual instances without any additional schema definition:
        {{schema}}
        Make sure your response is a dict and not a list.
        {% if invalid_replies and error_message %}
          You already created the following output in a previous attempt: {{invalid_replies}}
          However, this doesn't comply with the format requirements from above and triggered this Python exception: {{error_message}}
          Correct the output and try again. Just return the corrected output without any extra explanations.
        {% endif %}
        """
        prompt_builder = PromptBuilder(template=prompt_template)

        generator = OllamaGenerator(model="notus:7b-v1-q4_K_M",
                                    url="http://192.168.68.107:11434/api/generate")

        pipeline = Pipeline(max_loops_allowed=3)

        # Add components to your pipeline
        pipeline.add_component(instance=prompt_builder, name="prompt_builder")
        pipeline.add_component(instance=generator, name="llm")
        pipeline.add_component(instance=output_validator, name="output_validator")

        # Now, connect the components to each other
        pipeline.connect("prompt_builder", "llm")
        pipeline.connect("llm", "output_validator")
        # If a component has more than one output or input, explicitly specify the connections:
        pipeline.connect("output_validator.invalid_replies", "prompt_builder.invalid_replies")
        pipeline.connect("output_validator.error_message", "prompt_builder.error_message")

        # pipeline.draw("auto-correct-pipeline.png")

        passage = ("Berlin is the capital of Germany. It has a population of 3,850,809. Paris, France's capital, "
                   "has 2.161 million residents. Lisbon is the capital and the largest city of Portugal with the population of 504,718.")
        result = pipeline.run({"prompt_builder": {"passage": passage, "schema": json_schema}})

        valid_reply = result["output_validator"]["valid_replies"][0]
        valid_json = json.loads(valid_reply)
        print("\nValid JSON:")
        print(valid_json)

        return '{"answer": "Not implemented yet"}'
