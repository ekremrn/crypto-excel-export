import os
import logging
import pandas as pd
from time import sleep
from typing import Dict, List, Optional
from functools import wraps
from io import BytesIO
from datetime import datetime

from binance.client import Client
from requests.exceptions import RequestException
from binance.exceptions import BinanceAPIException

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

KLINE_COLUMNS = [
    "OpenTime",
    "Open", 
    "High",
    "Low",
    "Close",
    "Volume",
    "CloseTime",
    "QuoteAssetVolume",
    "NumberOfTrades",
    "TakerBuyBaseAssetVolume",
    "TakerBuyQuoteAssetVolume",
    "CanBeIgnored",
]

NUMERIC_COLUMNS = [
    'Open', 'High', 'Low', 'Close', 'Volume', 'QuoteAssetVolume', 
    'NumberOfTrades', 'TakerBuyBaseAssetVolume', 'TakerBuyQuoteAssetVolume'
]

def retry_on_api_error(max_retries: int = 3, delay: float = 1.0):
    """Decorator to retry API calls on failure"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (RequestException, BinanceAPIException) as e:
                    last_exception = e
                    logger.warning(f"API call failed (attempt {attempt + 1}/{max_retries}): {e}")
                    if attempt < max_retries - 1:
                        sleep(delay * (2 ** attempt))  # Exponential backoff
                except Exception as e:
                    logger.error(f"Unexpected error in {func.__name__}: {e}")
                    raise
            
            logger.error(f"All {max_retries} attempts failed for {func.__name__}")
            raise last_exception
        return wrapper
    return decorator

class BinanceReadService:
    """Enhanced Binance API service for fetching and exporting historical data."""
    
    def __init__(self, testnet: bool = False) -> None:
        self.api_key = os.getenv("BINANCE_API_KEY")
        self.api_secret = os.getenv("BINANCE_API_SECRET")
        self.testnet = testnet or os.getenv("BINANCE_TESTNET", "").lower() == "true"
        
        try:
            self._client = Client(
                self.api_key, 
                self.api_secret,
                testnet=self.testnet
            )
            logger.info(f"Binance client initialized (testnet: {self.testnet})")
        except Exception as e:
            logger.error(f"Failed to initialize Binance client: {e}")
            raise

    def _validate_symbol(self, symbol: str) -> str:
        """Validate and normalize symbol format"""
        if not symbol:
            raise ValueError("Symbol cannot be empty")
        
        symbol = symbol.upper().strip()
        return symbol

    def _kline_to_dict(self, kline: List) -> Dict:
        """Convert kline list to dictionary with proper column names"""
        return dict(zip(KLINE_COLUMNS, kline))

    def _process_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process raw DataFrame with proper data types and formatting"""
        if df.empty:
            return df
        
        df['OpenTime'] = pd.to_datetime(df['OpenTime'], unit='ms')
        df['CloseTime'] = pd.to_datetime(df['CloseTime'], unit='ms')
        
        for col in NUMERIC_COLUMNS:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col])
        
        if 'CanBeIgnored' in df.columns:
            df = df.drop('CanBeIgnored', axis=1)
        
        return df

    @retry_on_api_error(max_retries=3)
    def get_historical_klines(self, symbol: str, interval: str, start_time: str, 
                             end_time: Optional[str] = None) -> List[Dict]:
        """Get historical klines data, handling pagination to fetch all data in the range."""
        symbol = self._validate_symbol(symbol)
        
        all_klines = self._client.get_historical_klines(
            symbol=symbol,
            interval=interval,
            start_str=start_time,
            end_str=end_time
        )

        logger.info(f"Fetched a total of {len(all_klines)} klines for {symbol}")
        return [self._kline_to_dict(k) for k in all_klines]

    def get_historical_data_as_dataframe(self, symbol: str, interval: str, 
                                       start_date: str, end_date: Optional[str] = None) -> pd.DataFrame:
        """Get historical klines data as pandas DataFrame"""
        try:
            klines_data = self.get_historical_klines(symbol, interval, start_date, end_date)
            
            if not klines_data:
                return pd.DataFrame()
            
            df = pd.DataFrame(klines_data)
            df = self._process_dataframe(df)
            
            logger.info(f"Created DataFrame with {len(df)} rows for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Error creating DataFrame for {symbol}: {e}")
            return pd.DataFrame()

    def export_to_excel(self, symbol: str, interval: str, start_date: str, 
                       end_date: Optional[str] = None) -> Optional[bytes]:
        """Export historical data to Excel bytes"""
        try:
            df = self.get_historical_data_as_dataframe(symbol, interval, start_date, end_date)
            
            if df.empty:
                logger.warning(f"No data to export for {symbol}")
                return None
            
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name=f'{symbol}_{interval}', index=False)
                
                workbook = writer.book
                worksheet = writer.sheets[f'{symbol}_{interval}']
                
                header_format = workbook.add_format({
                    'bold': True,
                    'text_wrap': True,
                    'valign': 'top',
                    'fg_color': '#D7E4BC',
                    'border': 1
                })
                
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                
                for i, col in enumerate(df.columns):
                    max_len = max(df[col].astype(str).map(len).max(), len(col)) + 2
                    worksheet.set_column(i, i, min(max_len, 50))
            
            excel_data = output.getvalue()
            logger.info(f"Created Excel file for {symbol} ({len(excel_data)} bytes)")
            return excel_data
            
        except Exception as e:
            logger.error(f"Error creating Excel file for {symbol}: {e}")
            return None
        