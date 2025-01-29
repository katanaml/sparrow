from typing import Dict, List
from prefect import flow, task
import numpy as np
from datetime import datetime
from .market_client import MarketClient


@task(name="validate_trading_input")
async def validate_trading_input(input_data: Dict) -> Dict:
    """
    Validates trading input parameters
    """
    if not input_data.get('symbols'):
        raise ValueError("Symbols list is required")

    if not input_data.get('account_balance'):
        raise ValueError("Account balance is required")

    return {
        'symbols': input_data['symbols'],
        'account_balance': float(input_data['account_balance']),
        'risk_tolerance': float(input_data.get('risk_tolerance', 0.5))
    }


@task(name="analyze_market")
async def analyze_market(symbols: List[str], market_client: MarketClient) -> Dict:
    """
    Analyzes market data for given symbols
    """
    market_data = {}
    for symbol in symbols:
        data = await market_client.get_market_data(symbol)
        market_data[symbol] = {
            "price": data["price"],
            "volume": data["volume"],
            "indicators": await calculate_indicators(data["historical_prices"])
        }
    return market_data


@task(name="calculate_indicators")
async def calculate_indicators(prices: List[float]) -> Dict:
    """
    Calculates technical indicators for decision making
    """
    return {
        "sma_20": float(np.mean(prices[-20:])) if len(prices) >= 20 else None,
        "sma_50": float(np.mean(prices[-50:])) if len(prices) >= 50 else None,
        "volatility": float(np.std(prices))
    }


@task(name="generate_trading_decisions")
async def generate_trading_decisions(
        market_data: Dict,
        account_balance: float,
        risk_tolerance: float
) -> List[Dict]:
    """
    Generates trading decisions based on market analysis
    """
    decisions = []
    for symbol, data in market_data.items():
        if should_trade(data, risk_tolerance):
            decisions.append({
                "symbol": symbol,
                "action": "buy" if is_buy_signal(data) else "sell",
                "quantity": calculate_position_size(data, account_balance, risk_tolerance)
            })
    return decisions


def should_trade(data: Dict, risk_tolerance: float) -> bool:
    """
    Determines if we should trade based on market conditions
    """
    volatility = data.get('indicators', {}).get('volatility', 0)
    max_acceptable_volatility = 0.2 * (1 + risk_tolerance)
    return volatility <= max_acceptable_volatility


def is_buy_signal(data: Dict) -> bool:
    """
    Determines if current conditions indicate a buy signal
    """
    sma_20 = data.get('indicators', {}).get('sma_20')
    sma_50 = data.get('indicators', {}).get('sma_50')
    current_price = data.get('price')

    if not all([sma_20, sma_50, current_price]):
        return False

    return current_price > sma_20 > sma_50


def calculate_position_size(data: Dict, account_balance: float, risk_tolerance: float) -> float:
    """
    Calculates appropriate position size
    """
    base_position_size = account_balance * 0.02
    risk_adjusted_size = base_position_size * risk_tolerance

    volatility = data.get('indicators', {}).get('volatility', 0)
    if volatility > 0:
        risk_adjusted_size = risk_adjusted_size * (1 / volatility)

    current_price = data.get('price', 1)
    quantity = risk_adjusted_size / current_price

    return round(quantity, 2)


class TradingAgent:
    """
    Agent for automated trading execution
    """

    def __init__(self):
        self.name = "trading"
        self.capabilities = {"market_analysis", "trading_execution"}
        self.market_client = MarketClient()

    @flow(name="trading_flow")
    async def execute(self, input_data: Dict) -> Dict:
        """
        Main trading flow
        """
        # Validate input
        validated_input = await validate_trading_input(input_data)

        # Analyze market
        market_data = await analyze_market(
            validated_input['symbols'],
            self.market_client
        )

        # Generate decisions
        trading_decisions = await generate_trading_decisions(
            market_data,
            validated_input['account_balance'],
            validated_input['risk_tolerance']
        )

        return {
            "timestamp": datetime.now().isoformat(),
            "market_analysis": market_data,
            "trading_decisions": trading_decisions,
            "parameters_used": {
                "symbols": validated_input['symbols'],
                "risk_tolerance": validated_input['risk_tolerance']
            }
        }