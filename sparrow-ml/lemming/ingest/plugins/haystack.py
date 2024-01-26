from ingest.plugins.interface import Ingest


class HaystackIngest(Ingest):
    def run_ingest(self, payload: str) -> None:
        print(f"Running ingest with {payload}")
