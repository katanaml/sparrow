from rag.agents.interface import Pipeline
from openai import OpenAI
from pydantic import BaseModel, Field
import yfinance as yf
import instructor
import timeit
import box
import yaml
from rich import print
from typing import Any, List
import warnings


warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)


class Stocks(Pipeline):
    def run_pipeline(self,
                     agent: str,
                     query: str,
                     file_path: str,
                     options: List[str] = None,
                     crop_size: int = None,
                     debug_dir: str = None,
                     debug: bool = False,
                     local: bool = True) -> Any:
        print(f"\nRunning pipeline with {agent}\n")

        # Import config vars
        with open('config.yml', 'r', encoding='utf8') as ymlfile:
            cfg = box.Box(yaml.safe_load(ymlfile))

        start = timeit.default_timer()

        company = query

        class StockInfo(BaseModel):
            company: str = Field(..., description="Name of the company")
            ticker: str = Field(..., description="Ticker symbol of the company")

        # enables `response_model` in create call
        client = instructor.patch(
            OpenAI(
                base_url=cfg.OLLAMA_BASE_URL_FUNCTION,
                api_key="ollama",
            ),
            mode=instructor.Mode.JSON,
        )

        resp = client.chat.completions.create(
            model=cfg.LLM_FUNCTION,
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
