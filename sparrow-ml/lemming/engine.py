import timeit
from rag.pipeline import build_rag_pipeline
import json
import time
import warnings
import typer
from typing_extensions import Annotated
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print


warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)


def get_rag_response(query, chain, debug=False):
    result = chain.query(query)

    try:
        # Convert and pretty print
        data = json.loads(str(result))
        data = json.dumps(data, indent=4)
        return data
    except (json.decoder.JSONDecodeError, TypeError):
        print("The response is not in JSON format:\n")
        print(result)

    return False


def run(inputs: Annotated[str, typer.Argument(help="The list of fields to fetch")],
        types: Annotated[str, typer.Argument(help="The list of types of the fields")],
        debug: Annotated[bool, typer.Argument(help="Enable debug mode")] = False):

    start = timeit.default_timer()

    query = 'retrieve ' + inputs
    query_types = types

    query_inputs_arr = [param.strip() for param in inputs.split(',')]
    query_types_arr = [param.strip() for param in query_types.split(',')]

    rag_chain = build_rag_pipeline(query_inputs_arr, query_types_arr, debug)

    end = timeit.default_timer()
    print(f"Time to prepare RAG pipeline: {end - start}")

    process_query(query, rag_chain, debug)


def process_query(query, rag_chain, debug=False, local=True):
    start = timeit.default_timer()

    step = 0
    answer = False
    while not answer:
        step += 1
        if step > 1:
            print('Refining answer...')
            # add wait time, before refining to avoid spamming the server
            time.sleep(5)
        if step > 3:
            # if we have refined 3 times, and still no answer, break
            answer = 'No answer found.'
            break

        if local:
            with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    transient=False,
            ) as progress:
                progress.add_task(description="Retrieving answer...", total=None)
                answer = get_rag_response(query, rag_chain, debug)
        else:
            print('Retrieving answer...')
            answer = get_rag_response(query, rag_chain, debug)

    end = timeit.default_timer()

    print(f"\nJSON response:\n")
    print(answer + '\n')
    print('=' * 50)

    print(f"Time to retrieve answer: {end - start}")

    return answer


if __name__ == "__main__":
    typer.run(run)
