import warnings
import typer
import json
from typing_extensions import Annotated, List
from pipelines.interface import get_pipeline
import tempfile
import os
from rich import print
from pipelines.sparrow_parse.sparrow_utils import (
    add_page_number
)


# Disable parallelism in the Huggingface tokenizers library to prevent potential deadlocks and ensure consistent behavior.
# This is especially important in environments where multiprocessing is used, as forking after parallelism can lead to issues.
# Note: Disabling parallelism may impact performance, but it ensures safer and more predictable execution.
os.environ['TOKENIZERS_PARALLELISM'] = 'false'


warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)


def run(query: Annotated[str, typer.Argument(help="The list of fields to fetch")],
        file_path: Annotated[str, typer.Option(help="The file to process")] = None,
        pipeline: Annotated[str, typer.Option(help="Selected pipeline")] = "sparrow-parse",
        options: Annotated[List[str], typer.Option(help="Options to pass to the pipeline")] = None,
        crop_size: Annotated[int, typer.Option(help="Crop size for table extraction")] = None,
        instruction: Annotated[bool, typer.Option(help="Enable instruction query")] = False,
        validation: Annotated[bool, typer.Option(help="Enable validation query")] = False,
        ocr: Annotated[bool, typer.Option(help="Enable data ocr enhancement")] = False,
        markdown: Annotated[bool, typer.Option(help="Enable markdown output")] = False,
        page_type: Annotated[List[str], typer.Option(help="Page type query")] = None,
        debug_dir: Annotated[str, typer.Option(help="Debug folder for multipage")] = None,
        debug: Annotated[bool, typer.Option(help="Enable debug mode")] = False):

    user_selected_pipeline = pipeline  # Modify this as needed

    try:
        rag = get_pipeline(user_selected_pipeline)

        if markdown:
            answer = process_markdown_extraction(rag, user_selected_pipeline, query, file_path, options, crop_size,
                                                instruction, validation, ocr, markdown, page_type, debug_dir, debug)
        else:
            answer = rag.run_pipeline(user_selected_pipeline, query, file_path, options, crop_size, instruction, validation,
                                      ocr, markdown, page_type, debug_dir, debug, False)

        print(f"\nSparrow response:\n")
        print(answer)
    except ValueError as e:
        print(f"Caught an exception: {e}")


def process_markdown_extraction(rag, user_selected_pipeline, query, file_path, options, crop_size,
                               instruction, validation, ocr, markdown, page_type, debug_dir, debug):
    """
    Process document with markdown extraction and structured data extraction.

    Args:
        rag: Pipeline instance
        user_selected_pipeline: Name of the pipeline to use
        query: Schema query for data extraction
        file_path: Path to the document file
        options: Pipeline options
        crop_size: Crop size for table extraction
        instruction: Enable instruction query
        validation: Enable validation query
        ocr: Enable data ocr enhancement
        markdown: Enable markdown output
        page_type: Page type query
        debug_dir: Debug folder for multipage
        debug: Enable debug mode

    Returns:
        Extracted data as JSON string or dict
    """
    if debug:
        print("\nProcessing markdown with DeepSeek OCR...")

    markdown_options = [options[0], 'deepseek-ocr:latest']
    markdown_output_list, num_pages = rag.run_pipeline(user_selected_pipeline, query, file_path, markdown_options, crop_size,
                                       instruction, validation, ocr, markdown, page_type, debug_dir, debug, False)

    combined_output = []
    markdown_output_list = [markdown_output_list] if num_pages == 1 else markdown_output_list
    markdown_output_list = json.loads(markdown_output_list) if isinstance(markdown_output_list, str) else markdown_output_list

    for i, markdown_output in enumerate(markdown_output_list):
        instruction_query = create_extraction_prompt(markdown_content=markdown_output, schema_query=query)

        if debug:
            print("\nInstruction query:\n")
            print(instruction_query)

        rag = get_pipeline("sparrow-instructor")
        answer = rag.run_pipeline("sparrow-instructor", instruction_query, None, options, crop_size,
                                  instruction, validation, ocr, markdown, page_type, debug_dir, debug, False)

        if num_pages > 1:
            try:
                answer = json.loads(answer) if isinstance(answer, str) else answer
            except json.JSONDecodeError:
                answer = {
                    "message": "Invalid JSON format in LLM output",
                    "valid": "false"
                }
            answer = add_page_number(answer, i + 1)
            combined_output.append(answer)

    if num_pages > 1:
        answer = json.dumps(combined_output, indent=4, ensure_ascii=False)

    return answer


def create_extraction_prompt(markdown_content: str, schema_query: str) -> str:
    """
    Generate a prompt for LLM to extract structured data from markdown.

    Args:
        markdown_content: The markdown text to extract data from
        schema_query: JSON schema string defining the structure of data to extract

    Returns:
        A formatted prompt string with instruction and payload sections

    Example:
        >>> markdown = "<table><tr><td>Name</td><td>Age</td></tr>...</table>"
        >>> schema = '[{"name": "str", "age": "int"}]'
        >>> prompt = create_extraction_prompt(markdown, schema)
    """
    # Build the instruction section
    instruction = f"""instruction:
You are a data extraction specialist. Your task is to analyze the provided markdown content and extract structured data according to the specified JSON schema.

Guidelines:
- Carefully parse all content in the markdown, including tables, lists, and formatted text
- Extract data that matches the structure defined in the schema query
- Ensure data types match the schema specifications (str, int, float, bool, etc.)
- If a field is not present or cannot be determined, use null
- Return ONLY valid JSON that conforms to the schema
- Preserve numerical accuracy and formatting where relevant
- Handle special characters and unicode properly

Schema Query:
{schema_query}

Output Format:
Return a JSON object or array matching the schema structure. Do not include any explanatory text, markdown formatting, or code blocks - only the raw JSON data."""

    # Build the payload section
    payload = f"""payload:
{markdown_content}"""

    # Combine into final prompt
    prompt = f"{instruction}\n\n{payload}"

    return prompt


async def run_from_api_engine(user_selected_pipeline, query, options_arr, crop_size, instruction, validation, ocr, markdown, page_type, file, debug_dir, debug):
    try:
        rag = get_pipeline(user_selected_pipeline)

        if file is not None:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_file_path = os.path.join(temp_dir, file.filename)

                # Save the uploaded file to the temporary directory
                with open(temp_file_path, 'wb') as temp_file:
                    content = await file.read()
                    temp_file.write(content)

                if markdown:
                    markdown_options = [options_arr[0], 'deepseek-ocr:latest']
                    answer = process_markdown_extraction(rag, user_selected_pipeline, query, temp_file_path, markdown_options,
                                                         crop_size, instruction, validation, ocr, markdown, page_type, debug_dir,
                                                         debug)
                else:
                    answer = rag.run_pipeline(user_selected_pipeline, query, temp_file_path, options_arr, crop_size, instruction,
                                              validation, ocr, markdown, page_type, debug_dir, debug, False)
        else:
            answer = rag.run_pipeline(user_selected_pipeline, query, None, options_arr, crop_size, instruction,
                                      validation, ocr, markdown, page_type, debug_dir, debug, False)
    except ValueError as e:
        raise e

    return answer


# Add a new function for instruction-only processing
async def run_from_api_engine_instruction(user_selected_pipeline, query, options_arr, debug_dir, debug):
    """
    Instruction-only version of run_from_api_engine that doesn't require a file.
    """
    try:
        rag = get_pipeline(user_selected_pipeline)

        # Call run_pipeline with file_path=None for instruction-only processing
        answer = rag.run_pipeline(
            user_selected_pipeline,
            query,
            None,  # No file path for instruction-only queries
            options_arr,
            None,  # No crop_size needed
            False,  # No instruction needed
            False, # No validation needed
            False, # No ocr needed
            False, # No markdown needed
            None, # No page_type needed
            debug_dir,
            debug,
            False
        )
    except ValueError as e:
        raise e

    return answer


if __name__ == "__main__":
    typer.run(run)
