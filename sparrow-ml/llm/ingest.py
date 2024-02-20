import warnings
from ingest.agents.interface import get_ingest
import typer
from typing_extensions import Annotated


warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)


def run(agent: Annotated[str, typer.Option(help="Ingest agent")] = "llamaindex"):
    user_selected_agent = agent  # Modify this as needed
    ingest = get_ingest(user_selected_agent)
    ingest.run_ingest(user_selected_agent)


if __name__ == "__main__":
    typer.run(run)
