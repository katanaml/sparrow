import warnings
import typer
from typing_extensions import Annotated
from rag.agents.interface import get_pipeline

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)


def run(agent: Annotated[str, typer.Option(help="Ingest agent")] = "fcall",
        query: Annotated[str, typer.Option(help="The query to run")] = "retrieve",
        debug: Annotated[bool, typer.Option(help="Enable debug mode")] = False):
    user_selected_agent = agent  # Modify this as needed

    try:
        rag = get_pipeline(user_selected_agent)
        rag.run_pipeline(user_selected_agent, None, None, query, None, None, debug)
    except ValueError as e:
        print(f"Caught an exception: {e}")


if __name__ == "__main__":
    typer.run(run)