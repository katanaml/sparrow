from pipelines.interface import Pipeline
from openai import OpenAI
from pydantic import BaseModel, Field
import yfinance as yf
import instructor
import timeit
from rich import print
from typing import Any, List
import warnings
from config_utils import get_config


warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)


class Stocks(Pipeline):
    def run_pipeline(self,
                     pipeline: str,
                     query: str,
                     file_path: str,
                     hints_file_path: str = None,
                     options: List[str] = None,
                     crop_size: int = None,
                     instruction: bool = False,
                     validation: bool = False,
                     ocr: bool = False,
                     markdown: bool = False,
                     table: bool = False,
                     page_type: List[str] = None,
                     debug_dir: str = None,
                     debug: bool = False,
                     local: bool = True) -> Any:
        print(f"\nRunning pipeline with {pipeline}\n")

        # Get config instance
        config = get_config()

        start = timeit.default_timer()

        company = query

        class StockInfo(BaseModel):
            company: str = Field(..., description="Name of the company")
            ticker: str = Field(..., description="Ticker symbol of the company")

        # enables `response_model` in create call
        client = instructor.patch(
            OpenAI(
                base_url=config.get_str('settings', 'ollama_base_url'),
                api_key="ollama",
            ),
            mode=instructor.Mode.JSON,
        )

        resp = client.chat.completions.create(
            model=config.get_str('settings', 'llm_function'),
            messages=[
                {
                    "role": "user",
                    "content": f"Return the company name and the ticker symbol of the {company}."
                }
            ],
            response_model=StockInfo,
            max_retries=10
        )

        print(resp.model_dump_json(indent=2))
        stock = yf.Ticker(resp.ticker)
        hist = stock.history(period="1d")
        stock_price = hist['Close'].iloc[-1]
        print(f"The stock price of the {resp.company} is {stock_price}. USD")

        end = timeit.default_timer()

        print('=' * 50)

        print(f"Time to retrieve answer: {end - start}")
