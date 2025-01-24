import warnings
import typer
from typing_extensions import Annotated
from pipelines.interface import get_pipeline

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)


def run(pipeline: Annotated[str, typer.Option(help="Ingest pipeline")] = "stocks",
        query: Annotated[str, typer.Option(help="The query to run")] = "retrieve",
        debug: Annotated[bool, typer.Option(help="Enable debug mode")] = False):
    user_selected_pipeline = pipeline  # Modify this as needed

    try:
        rag = get_pipeline(user_selected_pipeline)
        rag.run_pipeline(user_selected_pipeline, query, None , None, debug, True)
    except ValueError as e:
        print(f"Caught an exception: {e}")


if __name__ == "__main__":
    typer.run(run)