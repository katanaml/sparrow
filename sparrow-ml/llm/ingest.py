import warnings
from embeddings.agents.interface import get_ingest
import typer
from typing_extensions import Annotated


warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)


def run(file_path: Annotated[str, typer.Option(help="The file to process")],
        agent: Annotated[str, typer.Option(help="Ingest agent")] = "llamaindex",
        index_name: Annotated[str, typer.Option(help="Index to identify embeddings")] = None):
    user_selected_agent = agent  # Modify this as needed
    ingest = get_ingest(user_selected_agent)
    ingest.run_ingest(user_selected_agent, file_path, index_name)


async def run_from_api_ingest(user_selected_agent, file, debug):
    pass


if __name__ == "__main__":
    typer.run(run)
