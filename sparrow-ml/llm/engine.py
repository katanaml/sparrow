import warnings
import typer
from typing_extensions import Annotated
from rag.agents.interface import get_pipeline
import tempfile
import os


warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)


def run(inputs: Annotated[str, typer.Argument(help="The list of fields to fetch")],
        types: Annotated[str, typer.Argument(help="The list of types of the fields")],
        file_path: Annotated[str, typer.Option(help="The file to process")] = None,
        agent: Annotated[str, typer.Option(help="Selected agent")] = "llamaindex",
        index_name: Annotated[str, typer.Option(help="Index to identify embeddings")] = None,
        options: Annotated[str, typer.Option(help="Options to pass to the agent")] = None,
        debug: Annotated[bool, typer.Option(help="Enable debug mode")] = False):

    query = 'retrieve ' + inputs
    query_types = types

    query_inputs_arr = [param.strip() for param in inputs.split(',')]
    query_types_arr = [param.strip() for param in query_types.split(',')]

    user_selected_agent = agent  # Modify this as needed

    try:
        rag = get_pipeline(user_selected_agent)
        rag.run_pipeline(user_selected_agent, query_inputs_arr, query_types_arr, query, file_path, index_name, options,
                         debug)
    except ValueError as e:
        print(f"Caught an exception: {e}")


async def run_from_api_engine(user_selected_agent, query_inputs_arr, query_types_arr, query, index_name, options,
                              file, debug):
    try:
        rag = get_pipeline(user_selected_agent)

        if file is not None:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_file_path = os.path.join(temp_dir, file.filename)

                # Save the uploaded file to the temporary directory
                with open(temp_file_path, 'wb') as temp_file:
                    content = await file.read()
                    temp_file.write(content)

                answer = rag.run_pipeline(user_selected_agent, query_inputs_arr, query_types_arr, query,
                                          temp_file_path, index_name, options, debug, False)
        else:
            answer = rag.run_pipeline(user_selected_agent, query_inputs_arr, query_types_arr, query, None,
                                      index_name, options, debug, False)
    except ValueError as e:
        raise e

    return answer


if __name__ == "__main__":
    typer.run(run)
