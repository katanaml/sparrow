import warnings
import typer
from typing_extensions import Annotated, List
from rag.agents.interface import get_pipeline
import tempfile
import os
from rich import print


# Disable parallelism in the Huggingface tokenizers library to prevent potential deadlocks and ensure consistent behavior.
# This is especially important in environments where multiprocessing is used, as forking after parallelism can lead to issues.
# Note: Disabling parallelism may impact performance, but it ensures safer and more predictable execution.
os.environ['TOKENIZERS_PARALLELISM'] = 'false'


warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)


def run(inputs: Annotated[str, typer.Argument(help="The list of fields to fetch")],
        types: Annotated[str, typer.Argument(help="The list of types of the fields")] = None,
        keywords: Annotated[str, typer.Argument(help="The list of table column keywords")] = None,
        file_path: Annotated[str, typer.Option(help="The file to process")] = None,
        agent: Annotated[str, typer.Option(help="Selected agent")] = "sparrow-parse",
        index_name: Annotated[str, typer.Option(help="Index to identify embeddings")] = None,
        options: Annotated[List[str], typer.Option(help="Options to pass to the agent")] = None,
        group_by_rows: Annotated[bool, typer.Option(help="Group JSON collection by rows")] = True,
        update_targets: Annotated[bool, typer.Option(help="Update targets")] = True,
        debug: Annotated[bool, typer.Option(help="Enable debug mode")] = False):

    query = 'retrieve ' + inputs
    query_types = types

    query_inputs_arr = [param.strip() for param in inputs.split(',')] if query_types else []
    query_types_arr = [param.strip() for param in query_types.split(',')] if query_types else []
    keywords_arr = [param.strip() for param in keywords.split(',')] if keywords is not None else None

    if not query_types:
        query = inputs

    user_selected_agent = agent  # Modify this as needed

    try:
        rag = get_pipeline(user_selected_agent)
        answer = rag.run_pipeline(user_selected_agent, query_inputs_arr, query_types_arr, keywords_arr, query, file_path,
                                  index_name, options, group_by_rows, update_targets, debug)

        print(f"\nJSON response:\n")
        print(answer)
    except ValueError as e:
        print(f"Caught an exception: {e}")


async def run_from_api_engine(user_selected_agent, query_inputs_arr, query_types_arr, keywords_arr, query, index_name,
                              options_arr, file, group_by_rows, update_targets, debug):
    try:
        rag = get_pipeline(user_selected_agent)

        if file is not None:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_file_path = os.path.join(temp_dir, file.filename)

                # Save the uploaded file to the temporary directory
                with open(temp_file_path, 'wb') as temp_file:
                    content = await file.read()
                    temp_file.write(content)

                answer = rag.run_pipeline(user_selected_agent, query_inputs_arr, query_types_arr, keywords_arr, query,
                                          temp_file_path, index_name, options_arr, group_by_rows, update_targets,
                                          debug, False)
        else:
            answer = rag.run_pipeline(user_selected_agent, query_inputs_arr, query_types_arr, keywords_arr, query,
                                      None, index_name, options_arr, group_by_rows, update_targets,
                                      debug, False)
    except ValueError as e:
        raise e

    return answer


if __name__ == "__main__":
    typer.run(run)
