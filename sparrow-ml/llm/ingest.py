import warnings
from ingest.plugins.interface import get_ingest
import typer
from typing_extensions import Annotated


warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)


def run(plugin: Annotated[str, typer.Argument(help="Ingest plugin")] = "LlamaIndex"):
    user_selected_plugin = plugin  # Modify this as needed
    ingest = get_ingest(user_selected_plugin)
    ingest.run_ingest(user_selected_plugin)


if __name__ == "__main__":
    typer.run(run)
