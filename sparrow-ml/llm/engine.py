import warnings
import typer
from typing_extensions import Annotated
from rag.plugins.interface import get_pipeline


warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)


def run(inputs: Annotated[str, typer.Argument(help="The list of fields to fetch")],
        types: Annotated[str, typer.Argument(help="The list of types of the fields")],
        plugin: Annotated[str, typer.Argument(help="Ingest plugin")] = "LlamaIndex",
        debug: Annotated[bool, typer.Argument(help="Enable debug mode")] = False):

    query = 'retrieve ' + inputs
    query_types = types

    query_inputs_arr = [param.strip() for param in inputs.split(',')]
    query_types_arr = [param.strip() for param in query_types.split(',')]

    user_selected_plugin = plugin  # Modify this as needed
    rag = get_pipeline(user_selected_plugin)
    rag.run_pipeline(user_selected_plugin, query_inputs_arr, query_types_arr, query, debug)


def run_from_api(user_selected_plugin, query_inputs_arr, query_types_arr, query, debug):
    rag = get_pipeline(user_selected_plugin)
    answer = rag.run_pipeline(user_selected_plugin, query_inputs_arr, query_types_arr, query, debug, False)
    return answer


if __name__ == "__main__":
    typer.run(run)
