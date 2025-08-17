# 📊 KuCoin Crypto Data Exporter

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://crypto-excel-export.streamlit.app/)

A simple web app built with [Streamlit](https://streamlit.io/) to download historical cryptocurrency k-line (candlestick) data from [KuCoin](https://www.kucoin.com/) and export it to a formatted Excel file.

## ✨ Features

- **KuCoin-Specific Data Fetching**: Designed to work seamlessly with the KuCoin API.
- **Date Range Selection**: Easily specify start and end dates to fetch historical data for any period.
- **Progress Bar**: Visual feedback during data download, especially useful for large date ranges.
- **Exports to Excel**: Downloads data into a well-formatted `.xlsx` file.
- **Easy-to-use UI**: Intuitive interface to select trading pair, time interval, and date range.

## 🚀 Quickstart

Follow these steps to run the app locally.

### 1. Clone & Setup

```bash
# Clone the repository
git clone https://github.com/your-username/crypto-excel-export.git
cd crypto-excel-export

# Install dependencies
pip install -r requirements.txt
```

### 2. Run the App

```bash
streamlit run streamlit_app.py
```

Navigate to `http://localhost:8501` in your browser.

### 3. Configuration (Optional)

This app can fetch public K-line data without API keys. However, providing your KuCoin API Key, Secret, and Passphrase will allow for higher rate limits and access to private endpoints if you extend the application.

1.  Copy `.env.example` to a new file named `.env`.
2.  Add your `KUCOIN_API_KEY`, `KUCOIN_API_SECRET`, and `KUCOIN_API_PASSPHRASE` to the `.env` file.

## 📝 License

This project is licensed under the [MIT License](LICENSE).