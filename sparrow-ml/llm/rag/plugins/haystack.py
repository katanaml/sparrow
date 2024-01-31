from rag.plugins.interface import Pipeline


class HaystackPipeline(Pipeline):
    def run_pipeline(self,
                     payload: str,
                     query_inputs: [str],
                     query_types: [str],
                     query: str,
                     debug: bool = False,
                     local: bool = True) -> None:
        print(f"\nRunning pipeline with {payload}\n")
