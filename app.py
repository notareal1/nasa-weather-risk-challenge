import streamlit as st
import pandas as pd
import datetime
import os

st.set_page_config(layout="wide", page_title="Đánh giá Rủi ro Khí hậu")

try:
    st.image('NASALOGO.png', width=150) 
except FileNotFoundError:
    st.error("LỖI: Không tìm thấy file NASALOGO.png.")
    
st.title("☀️ Ứng dụng Đánh giá Rủi ro Khí hậu (NASA Challenge)")
st.markdown("### Xác suất lịch sử của các điều kiện thời tiết cực đoan (1980-2010)")
st.markdown("---") 

RISK_FILES = {
    "NÓNG CỰC ĐOAN (Max Temp)": {'file': 'risk_stats_max.csv', 'icon': '🔥', 'type': 'trên', 'unit': ' °C'},
    "LẠNH CỰC ĐOAN (Min Temp)": {'file': 'risk_stats_min.csv', 'icon': '🧊', 'type': 'dưới', 'unit': ' °C'},
    "GIÓ MẠNH CỰC ĐOAN (Max Wind)": {'file': 'risk_stats_wind.csv', 'icon': '💨', 'type': 'trên', 'unit': ' m/s'},
    "HƠI NƯỚC CỰC ĐOAN (Water Vapor)": {'file': 'risk_stats_water_vapor.csv', 'icon': '💧', 'type': 'trên', 'unit': ' $kg/m^2$'},
    "MƯA CỰC ĐOAN (Rainfall)": {'file': 'risk_stats_rainfall.csv', 'icon': '🌧️', 'type': 'trên', 'unit': ' mm/ngày'}, 
}

risk_data = {}
all_data_loaded = True
for name, info in RISK_FILES.items():
    file_path = info['file']
    try:
        df = pd.read_csv(file_path, index_col=[0, 1])
        risk_data[name] = df
    except FileNotFoundError:
        st.error(f"LỖI TẢI DỮ LIỆU: Không tìm thấy file **{file_path}**. Vui lòng đảm bảo đã chạy `risk_analyzer.py` thành công.")
        all_data_loaded = False
        break
    except Exception as e:
        st.error(f"LỖI ĐỊNH DẠNG FILE **{file_path}**: {e}")
        all_data_loaded = False
        break

if all_data_loaded:
    
    st.sidebar.header("Tùy chọn Truy vấn")
    
    today = datetime.date.today()
    date_input = st.sidebar.date_input(
        "Chọn Ngày/Tháng bạn quan tâm:",
        today
    )

    if date_input is not None:
        selected_month = date_input.month
        selected_day = date_input.day
    else:
        selected_month = today.month
        selected_day = today.day

    st.subheader(f"Báo cáo Rủi ro cho ngày **{selected_day:02d}** tháng **{selected_month:02d}**")
    st.markdown("---")

    cols = st.columns(5)
    
    risk_names = list(risk_data.keys())
    
    for i, name in enumerate(risk_names):
        df = risk_data[name]
        with cols[i]:
            st.markdown(f"**{RISK_FILES[name]['icon']} {name}**")
            st.markdown("---", unsafe_allow_html=True)
            
            try:
                threshold_col = [col for col in df.columns if 'Risk_Threshold' in col]
                if not threshold_col:
                    st.error("Lỗi: Không tìm thấy cột ngưỡng trong file CSV.")
                    continue
                threshold_col = threshold_col[0]

                risk_row = df.loc[(selected_month, selected_day)]
                
                threshold_val = risk_row[threshold_col]
                unit = RISK_FILES[name]['unit']
                risk_type = RISK_FILES[name]['type']
                
                st.info(f"Ngưỡng Rủi ro ({risk_type}): **{threshold_val:.2f}{unit}**")

                historical_prob = risk_row['Historical_Prob_%']
                theoretical_prob = risk_row['Theoretical_Risk_Prob_%']
                
                delta_str = f"Lý thuyết: {theoretical_prob:.2f}%"
                
                st.metric(
                    label="Xác suất Lịch sử:",
                    value=f"{historical_prob:.2f}%",
                    delta=delta_str,
                    delta_color="off"
                )
                
            except KeyError:
                st.warning("Không tìm thấy dữ liệu rủi ro cho ngày này (Kiểm tra dữ liệu gốc thiếu hoặc lỗi 29/02).")
            except Exception:
                st.error("Lỗi dữ liệu không xác định. Vui lòng kiểm tra lại file CSV.")

    st.markdown("---")
    st.subheader("Tùy chọn Tải Dữ liệu")
    st.markdown("Người dùng có thể tải xuống toàn bộ dữ liệu phân tích đã tính toán.")
    
    cols_dl = st.columns(5)
    
    for i, name in enumerate(risk_names):
        df = risk_data[name]
        with cols_dl[i]:
            st.download_button(
                label=f"Tải {RISK_FILES[name]['icon']} {name.split('(')[0].strip()} (CSV)",
                data=df.to_csv().encode('utf-8'),
                file_name=f'risk_analysis_{name.split()[0].lower()}.csv',
                mime='text/csv'
            )