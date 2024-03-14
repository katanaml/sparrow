import warnings
from embeddings.agents.interface import get_ingest
import typer
from typing_extensions import Annotated
import tempfile
import os


warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)


def run(file_path: Annotated[str, typer.Option(help="The file to process")],
        agent: Annotated[str, typer.Option(help="Ingest agent")] = "llamaindex",
        index_name: Annotated[str, typer.Option(help="Index to identify embeddings")] = None):
    user_selected_agent = agent  # Modify this as needed
    ingest = get_ingest(user_selected_agent)
    ingest.run_ingest(user_selected_agent, file_path, index_name)


async def run_from_api_ingest(agent, index_name, file, debug):
    try:
        user_selected_agent = agent  # Modify this as needed
        ingest = get_ingest(user_selected_agent)

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file_path = os.path.join(temp_dir, file.filename)

            # Save the uploaded file to the temporary directory
            with open(temp_file_path, 'wb') as temp_file:
                content = await file.read()
                temp_file.write(content)

            ingest.run_ingest(user_selected_agent, temp_file_path, index_name)
    except ValueError as e:
        raise e

    return {"message": "Ingested successfully"}


if __name__ == "__main__":
    typer.run(run)
