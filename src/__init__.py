"""
F&O Trading Bot Package

A professional-grade trading agent for Futures & Options using Zerodha Kite Connect API.
"""

__version__ = '1.0.0'
__author__ = 'Trading Bot Team'

from src.main import TradingBot
from src.strategy import Strategy
from src.order_manager import OrderManager
from src.position_manager import PositionManager
from src.risk_manager import RiskManager
from src.data_handler import DataHandler
from src.backtester import Backtester
from src.zerodha_api import ZerodhaAPI
from src.zerodha_auth import ZerodhaAuth, SessionManager
from src.zerodha_mock import MockZerodhaAPI
from src.trade_journal import TradeJournal
from src.market_analyzer import MarketAnalyzer
from src.paper_trading_engine import PaperTradingEngine

__all__ = [
    'TradingBot',
    'Strategy',
    'OrderManager',
    'PositionManager',
    'RiskManager',
    'DataHandler',
    'Backtester',
    'ZerodhaAPI',
    'ZerodhaAuth',
    'SessionManager',
    'MockZerodhaAPI',
    'TradeJournal',
    'MarketAnalyzer',
    'PaperTradingEngine'
]
