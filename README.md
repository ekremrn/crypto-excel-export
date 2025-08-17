# 📊 Crypto Data Exporter

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A simple web app built with [Streamlit](https://streamlit.io/) to download historical cryptocurrency k-line data from [Binance](https://www.binance.com/) and export it to a formatted Excel file.

## ✨ Features

- **Easy-to-use UI** to select a trading pair, time interval, and start date.
- **Fetches historical data** for any symbol available on Binance.
- **Exports to Excel**: Downloads data into a well-formatted `.xlsx` file.
- **Data Preview**: Displays the first 10 rows and basic stats before downloading.

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

This app works with public data and does not require API keys. However, you can add your own Binance keys for higher request limits.

1.  Copy `.env.example` to a new file named `.env`.
2.  Add your `BINANCE_API_KEY` and `BINANCE_API_SECRET` to the `.env` file.

## 📝 License

This project is licensed under the [MIT License](LICENSE).