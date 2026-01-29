import json
from pipelines.interface import get_pipeline
from pipelines.sparrow_parse.sparrow_utils import add_page_number


def read_hints_from_json(hints_file_path: str) -> str:
    """
    Check if hints_file_path points to a JSON file and read its content.

    Args:
        hints_file_path: Path to the hints file

    Returns:
        Content of the JSON file as a string, or empty string if not a JSON file or file doesn't exist
    """
    if hints_file_path and hints_file_path.endswith('.json'):
        try:
            with open(hints_file_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
                return json.dumps(content, ensure_ascii=False)
        except (FileNotFoundError, json.JSONDecodeError, IOError):
            return ""
    return ""


def process_markdown_extraction(rag, user_selected_pipeline, query, file_path, hints_file_path, options, crop_size,
                               instruction, validation, ocr, markdown, page_type, debug_dir, debug):
    """
    Process document with markdown extraction and structured data extraction.

    Args:
        rag: Pipeline instance
        user_selected_pipeline: Name of the pipeline to use
        query: Schema query for data extraction
        file_path: Path to the document file
        hints_file_path: Path to JSON file containing query hints
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
    markdown_output_list = rag.run_pipeline(user_selected_pipeline, query, file_path, hints_file_path, markdown_options,
                                            crop_size, instruction, validation, ocr, markdown, page_type, debug_dir,
                                            debug, False)

    combined_output = []
    try:
        markdown_output_list = json.loads(markdown_output_list) if isinstance(markdown_output_list, str) else markdown_output_list
    except (json.JSONDecodeError, ValueError):
        pass
    markdown_output_list = [markdown_output_list] if not isinstance(markdown_output_list, list) else markdown_output_list
    num_pages = len(markdown_output_list)

    for i, markdown_output in enumerate(markdown_output_list):
        instruction_query = create_extraction_prompt(markdown_content=markdown_output, schema_query=query, hints_file_path=hints_file_path)

        if debug:
            print("\nInstruction query:\n")
            print(instruction_query)

        rag = get_pipeline("sparrow-instructor")
        answer = rag.run_pipeline("sparrow-instructor", instruction_query, None, None, options, crop_size,
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


def create_extraction_prompt(markdown_content: str, schema_query: str, hints_file_path: str = None) -> str:
    """
    Generate a prompt for LLM to extract structured data from markdown.

    Args:
        markdown_content: The markdown text to extract data from
        schema_query: JSON schema string defining the structure of data to extract
        hints_file_path: Optional path to JSON file containing query hints

    Returns:
        A formatted prompt string with instruction and payload sections

    Example:
        >>> markdown = "<table><tr><td>Name</td><td>Age</td></tr>...</table>"
        >>> schema = '[{"name": "str", "age": "int"}]'
        >>> prompt = create_extraction_prompt(markdown, schema)
    """
    # Read hints from JSON file if provided
    hints_content = read_hints_from_json(hints_file_path)
    hints_section = f"\n\nAdditional Hints:\n{hints_content}" if hints_content else ""

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
{schema_query}{hints_section}

Output Format:
Return a JSON object or array matching the schema structure. Do not include any explanatory text, markdown formatting, or code blocks - only the raw JSON data."""

    # Build the payload section
    payload = f"""payload:
{markdown_content}"""

    # Combine into final prompt
    prompt = f"{instruction}\n\n{payload}"

    return prompt
