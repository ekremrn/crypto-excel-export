import logging
import pandas as pd
from io import BytesIO
from kucoin.client import Client
import time
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KuCoinService:
    """Service for fetching and exporting crypto data from KuCoin."""
    
    def __init__(self, api_key: str = "", api_secret: str = "", api_passphrase: str = ""):
        try:
            if api_key and api_secret and api_passphrase:
                self._client = Client(api_key, api_secret, api_passphrase)
                logger.info("KuCoin client initialized with credentials.")
            else:
                # Initialize without credentials for public endpoints
                self._client = Client()
                logger.info("KuCoin client initialized for public data access.")
        except Exception as e:
            logger.error(f"Failed to initialize KuCoin client: {e}")
            raise

    def _format_symbol(self, pair: str) -> str:
        """Formats a trading pair like 'BTCUSDT' to KuCoin's 'BTC-USDT' format."""
        pair = pair.upper()
        bases = ['USDT', 'USDC', 'TUSD', 'BUSD', 'BTC', 'ETH', 'KCS']
        for base in bases:
            if pair.endswith(base) and len(pair) > len(base):
                return f"{pair[:-len(base)]}-{base}"
        if len(pair) > 3:
             return f"{pair[:-3]}-{pair[-3:]}"
        return pair

    def get_kline_data_as_dataframe(self, trading_pair: str, interval: str, start_at: datetime, end_at: datetime, progress_callback=None) -> pd.DataFrame:
        """
        Fetches K-line (candlestick) data for a given trading pair, interval, and date range,
        handling pagination by fetching data in chunks.
        """
        symbol = self._format_symbol(trading_pair)
        logger.info(f"Fetching K-line data for symbol '{symbol}' from {start_at} to {end_at} with interval '{interval}'.")

        all_data = []
        
        # KuCoin API returns a maximum of 1500 data points per request
        limit = 1500
        
        start_at_ts = int(start_at.timestamp())
        end_at_ts = int(end_at.timestamp())
        
        total_duration = end_at_ts - start_at_ts
        
        current_end_ts = end_at_ts

        while current_end_ts > start_at_ts:
            try:
                # Fetch data from current_end_ts backwards
                kline_chunk = self._client.get_kline_data(
                    symbol,
                    interval,
                    endAt=current_end_ts,
                    startAt=start_at_ts # We still need a start, the API will limit the result to 1500 points from the end
                )

                if not kline_chunk:
                    logger.warning(f"No more K-line data found for {symbol} in the current chunk.")
                    break

                all_data.extend(kline_chunk)
                
                # Get the timestamp of the oldest data point in the chunk
                oldest_ts_in_chunk = int(kline_chunk[-1][0])

                if progress_callback:
                    elapsed_duration = end_at_ts - oldest_ts_in_chunk
                    progress = min(elapsed_duration / total_duration, 1.0)
                    progress_callback(progress, f"Fetched data up to {datetime.fromtimestamp(oldest_ts_in_chunk).strftime('%Y-%m-%d')}...")

                # If the oldest data is older than our start date, we can stop
                if oldest_ts_in_chunk <= start_at_ts:
                    break
                
                # Set the end for the next chunk to be just before the oldest data we just received
                current_end_ts = oldest_ts_in_chunk - 1
                
                time.sleep(0.3) # Respect API rate limits

            except Exception as e:
                logger.error(f"Error fetching K-line data chunk from KuCoin for {symbol}: {e}")
                # Decide if we should break or continue
                break
        
        if not all_data:
            return pd.DataFrame()

        # Clean up and format the DataFrame
        df = pd.DataFrame(all_data, columns=['Timestamp', 'Open', 'Close', 'High', 'Low', 'Amount', 'Volume'])
        df.drop_duplicates(subset=['Timestamp'], inplace=True)

        for col in ['Open', 'Close', 'High', 'Low', 'Amount', 'Volume']:
            df[col] = pd.to_numeric(df[col])

        df['Timestamp'] = pd.to_datetime(df['Timestamp'].astype(int), unit='s')
        
        # Filter final dataframe to be strictly within the requested date range
        df = df[(df['Timestamp'] >= start_at) & (df['Timestamp'] <= end_at)]
        
        df = df.sort_values(by='Timestamp', ascending=True)
        df = df[['Timestamp', 'Open', 'High', 'Low', 'Close', 'Amount', 'Volume']]

        logger.info(f"Created DataFrame with {len(df)} rows for {symbol}")
        return df

    def export_to_excel(self, trading_pair: str, interval: str, start_at: datetime, end_at: datetime, progress_callback=None) -> bytes | None:
        """Exports historical K-line data to an Excel file in bytes."""
        df = self.get_kline_data_as_dataframe(trading_pair, interval, start_at, end_at, progress_callback)
        
        if df.empty:
            logger.warning(f"No data to export for {trading_pair}")
            return None
        
        output = BytesIO()
        sheet_name = f"{trading_pair[:15]}_{interval}"

        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            workbook = writer.book
            worksheet = writer.sheets[sheet_name]
            
            header_format = workbook.add_format({'bold': True, 'text_wrap': True, 'valign': 'top', 'fg_color': '#D7E4BC', 'border': 1})
            
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
            
            for i, col in enumerate(df.columns):
                if 'Timestamp' in str(df.columns[i]):
                    worksheet.set_column(i, i, 20)
                else:
                    max_len = max(df[col].astype(str).map(len).max(), len(col)) + 2
                    worksheet.set_column(i, i, min(max_len, 50))
        
        excel_data = output.getvalue()
        logger.info(f"Created Excel file for {trading_pair} ({len(excel_data)} bytes)")
        return excel_data