import streamlit as st
from datetime import date
from binance_service import BinanceReadService

st.set_page_config(page_title="Crypto Data Exporter", layout="centered", page_icon="📊")

# --- Service Initialization ---
@st.cache_resource
def get_binance_service():
    return BinanceReadService()

service = get_binance_service()

# --- UI ---
st.title("📊 Crypto Data Exporter")
st.markdown("Download historical Binance Futures k-line data to an Excel file.")

# --- Settings Form ---
with st.form(key="download_form"):
    st.subheader("1. Configure Data")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        symbol = st.text_input(
            "Trading Pair (e.g., BTCUSDT)",
            value="BTCUSDT",
        ).upper().strip()
        
    with col2:
        interval = st.selectbox(
            "Time Interval",
            options=["5m", "15m", "30m", "1h", "4h", "1d", "1w"],
            index=6,  # Default to 1d
        )

    start_date = st.date_input(
        "Start Date",
        value=date(2019, 1, 1),
        help="Select the start date for the data download. Data will be fetched up to the present day."
    )

    st.subheader("2. Generate Data")
    submitted = st.form_submit_button(
        "Generate Excel File", 
        type="primary", 
        use_container_width=True
    )

# --- Data Processing and Download ---
if submitted:
    if not symbol:
        st.error("❌ Please enter a trading pair!")
    elif start_date > date.today():
        st.error("❌ Start date cannot be in the future!")
    else:
        start_str = start_date.strftime("%d %B %Y")

        with st.spinner(f"📡 Fetching all historical data for {symbol} from {start_str}..."):
            try:
                df = service.get_historical_data_as_dataframe(symbol, interval, start_str)

                if df.empty:
                    st.error("❌ No data found for the specified symbol and date range!")
                else:
                    st.success(f"✅ Found {len(df)} data points!")

                    with st.spinner("📋 Creating Excel file..."):
                        excel_data = service.export_to_excel(symbol, interval, start_str)

                        if excel_data:
                            filename = f"{symbol}_{interval}_{start_date.strftime('%Y%m%d')}_to_today.xlsx"
                            
                            st.download_button(
                                label="💾 Download Excel File",
                                data=excel_data,
                                file_name=filename,
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                use_container_width=True
                            )

                            with st.expander("👁️ Preview Data (First 10 Rows)"):
                                st.dataframe(df.head(10), use_container_width=True)
                            
                            with st.expander("📊 Data Statistics"):
                                col1, col2 = st.columns(2)
                                col1.metric("Total Records", f"{len(df):,}")
                                col2.metric("File Size (KB)", f"{len(excel_data) / 1024:,.1f}")
                        else:
                            st.error("❌ Could not create the Excel file.")

            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")

# --- Footer ---
st.markdown("---")
st.caption("🔗 **Data Source:** Binance API | ⚠️ **Note:** Large date ranges may take time to download.")