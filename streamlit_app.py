import streamlit as st
from datetime import date, datetime, timedelta
from kucoin_service import KuCoinService

st.set_page_config(page_title="KuCoin Data Exporter", layout="centered", page_icon="📊")

# --- Service Initialization ---
@st.cache_resource
def get_kucoin_service():
    return KuCoinService()

service = get_kucoin_service()

# --- UI ---
st.title("📊 KuCoin Crypto Data Exporter")
st.markdown("Download historical KuCoin k-line data to an Excel file.")

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
            options=['1min', '3min', '5min', '15min', '30min', '1hour', '2hour', '4hour', '6hour', '8hour', '12hour', '1day', '1week', '1month'],
            index=11,  # Default to 1day
        )

    start_date = st.date_input(
        "Start Date",
        value=date.today() - timedelta(days=365),
        help="Select the start date for the data download."
    )

    end_date = st.date_input(
        "End Date",
        value=date.today(),
        help="Select the end date for the data download."
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
    elif start_date >= end_date:
        st.error("❌ Start date must be before end date!")
    elif start_date > date.today():
        st.error("❌ Start date cannot be in the future!")
    else:
        start_str = start_date.strftime("%d %B %Y")
        end_str = end_date.strftime("%d %B %Y")

        # Convert to datetime objects
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())

        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()

        def progress_callback(progress, message):
            progress_bar.progress(progress)
            status_text.text(message)

        with st.spinner(f"📡 Fetching data for {symbol} from {start_str} to {end_str}..."):
            try:
                excel_data = service.export_to_excel(symbol, interval, start_datetime, end_datetime, progress_callback)

                if excel_data:
                    # Get DataFrame for preview
                    df = service.get_kline_data_as_dataframe(symbol, interval, start_datetime, end_datetime)
                    
                    st.success(f"✅ Found {len(df)} data points!")

                    filename = f"KuCoin_{symbol}_{interval}_{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}.xlsx"
                    
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
                    st.error("❌ No data found for the specified symbol and date range!")

            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")
                st.exception(e)

        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()

# --- Footer ---
st.markdown("---")
st.caption("🔗 **Data Source:** KuCoin API | ⚠️ **Note:** Large date ranges may take time to download.")
