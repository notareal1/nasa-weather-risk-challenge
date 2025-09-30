import streamlit as st
import pandas as pd
import datetime
import os

# 1. TỪ ĐIỂN NGÔN NGỮ
LANGUAGES = {
    "VI": {
        "page_title": "Đánh giá Rủi ro Khí hậu",
        "app_title": "☀️ Ứng dụng Đánh giá Rủi ro Khí hậu (NASA Challenge)",
        "subtitle": "Xác suất lịch sử của các điều kiện thời tiết cực đoan (1980-2010)",
        "sidebar_header": "Tùy chọn Truy vấn",
        "date_input_label": "Chọn Ngày/Tháng bạn quan tâm:",
        "report_header": "Báo cáo Rủi ro cho ngày",
        "risk_threshold_label": "Ngưỡng Rủi ro",
        "historical_prob_label": "Xác suất Lịch sử:",
        "theoretical_label": "Lý thuyết",
        "download_header": "Tùy chọn Tải Dữ liệu",
        "download_info": "Người dùng có thể tải xuống toàn bộ dữ liệu phân tích đã tính toán.",
        "threshold_above": "trên",
        "threshold_below": "dưới",
        "loading_error": "LỖI TẢI DỮ LIỆU: Không tìm thấy file **{file}**.",
        "format_error": "LỖI ĐỊNH DẠNG FILE **{file}**:",
        "threshold_col_error": "Lỗi: Không tìm thấy cột ngưỡng trong file CSV.",
        "data_not_found": "Không tìm thấy dữ liệu rủi ro cho ngày này (Kiểm tra dữ liệu gốc thiếu hoặc lỗi 29/02).",
        "unknown_error": "Lỗi dữ liệu không xác định. Vui lòng kiểm tra lại file CSV.",
        "file_not_found_logo": "LỖI: Không tìm thấy file NASALOGO.png.",
        "risk_names": {
            "NÓNG CỰC ĐOAN (Max Temp)": "NÓNG CỰC ĐOAN (Max Temp)",
            "LẠNH CỰC ĐOAN (Min Temp)": "LẠNH CỰC ĐOAN (Min Temp)",
            "GIÓ MẠNH CỰC ĐOAN (Max Wind)": "GIÓ MẠNH CỰC ĐOAN (Max Wind)",
            "HƠI NƯỚC CỰC ĐOAN (Water Vapor)": "HƠI NƯỚC CỰC ĐOAN (Water Vapor)",
            "MƯA CỰC ĐOAN (Rainfall)": "MƯA CỰC ĐOAN (Rainfall)",
        }
    },
    "EN": {
        "page_title": "Climate Risk Analyzer",
        "app_title": "☀️ Climate Risk Analyzer (NASA Challenge)",
        "subtitle": "Historical probability of extreme weather conditions (1980-2010)",
        "sidebar_header": "Query Options",
        "date_input_label": "Select Date of Interest:",
        "report_header": "Risk Report for",
        "risk_threshold_label": "Risk Threshold",
        "historical_prob_label": "Historical Probability:",
        "theoretical_label": "Theoretical",
        "download_header": "Data Download Options",
        "download_info": "Users can download all pre-calculated risk analysis data.",
        "threshold_above": "above",
        "threshold_below": "below",
        "loading_error": "DATA LOADING ERROR: File **{file}** not found.",
        "format_error": "FILE FORMAT ERROR **{file}**:",
        "threshold_col_error": "Error: Threshold column not found in CSV file.",
        "data_not_found": "No risk data found for this date (Check for missing data or Feb 29 issue).",
        "unknown_error": "Unknown data error. Please check CSV files.",
        "file_not_found_logo": "ERROR: NASALOGO.png file not found.",
        "risk_names": {
            "NÓNG CỰC ĐOAN (Max Temp)": "EXTREME HEAT (Max Temp)",
            "LẠNH CỰC ĐOAN (Min Temp)": "EXTREME COLD (Min Temp)",
            "GIÓ MẠNH CỰC ĐOAN (Max Wind)": "EXTREME WIND (Max Wind)",
            "HƠI NƯỚC CỰC ĐOAN (Water Vapor)": "EXTREME WATER VAPOR (Water Vapor)",
            "MƯA CỰC ĐOAN (Rainfall)": "EXTREME RAINFALL (Rainfall)",
        }
    }
}

# 2. CHỌN NGÔN NGỮ
selected_lang_key = st.sidebar.selectbox(
    "Language / Ngôn ngữ",
    ["EN", "VI"],
    index=0 # Mặc định là Tiếng Anh cho Ban Giám khảo
)
lang = LANGUAGES[selected_lang_key]

def t(key, *args, **kwargs):
    """Hàm dịch thuật"""
    return lang[key].format(*args, **kwargs)

st.set_page_config(layout="wide", page_title=t("page_title"))

try:
    st.image('NASALOGO.png', width=150)
except FileNotFoundError:
    st.error(t("file_not_found_logo"))

st.title(t("app_title"))
st.markdown(f"### {t('subtitle')}")
st.markdown("---")

RISK_FILES = {
    # Dùng key là tên tiếng Việt gốc để đồng nhất với tên file, nhưng hiển thị bằng tên đã dịch
    "NÓNG CỰC ĐOAN (Max Temp)": {'file': 'risk_stats_max.csv', 'icon': '🔥', 'type_key': 'threshold_above', 'unit': ' °C'},
    "LẠNH CỰC ĐOAN (Min Temp)": {'file': 'risk_stats_min.csv', 'icon': '🧊', 'type_key': 'threshold_below', 'unit': ' °C'},
    "GIÓ MẠNH CỰC ĐOAN (Max Wind)": {'file': 'risk_stats_wind.csv', 'icon': '💨', 'type_key': 'threshold_above', 'unit': ' m/s'},
    "HƠI NƯỚC CỰC ĐOAN (Water Vapor)": {'file': 'risk_stats_water_vapor.csv', 'icon': '💧', 'type_key': 'threshold_above', 'unit': ' $kg/m^2$'},
    "MƯA CỰC ĐOAN (Rainfall)": {'file': 'risk_stats_rainfall.csv', 'icon': '🌧️', 'type_key': 'threshold_above', 'unit': ' mm/ngày'},
}

risk_data = {}
all_data_loaded = True
for name_vi, info in RISK_FILES.items():
    file_path = info['file']
    try:
        df = pd.read_csv(file_path, index_col=[0, 1])
        risk_data[name_vi] = df
    except FileNotFoundError:
        st.error(t("loading_error", file=file_path))
        all_data_loaded = False
        break
    except Exception as e:
        st.error(t("format_error", file=file_path) + f" {e}")
        all_data_loaded = False
        break

if all_data_loaded:

    st.sidebar.header(t("sidebar_header"))

    today = datetime.date.today()
    date_input = st.sidebar.date_input(
        t("date_input_label"),
        today
    )

    if date_input is not None:
        selected_month = date_input.month
        selected_day = date_input.day
    else:
        selected_month = today.month
        selected_day = today.day

    # Hiển thị ngày tháng theo định dạng
    st.subheader(f"{t('report_header')} **{selected_day:02d}** / **{selected_month:02d}**")
    st.markdown("---")

    cols = st.columns(5)

    risk_names_vi = list(risk_data.keys())

    for i, name_vi in enumerate(risk_names_vi):
        df = risk_data[name_vi]
        name_display = lang['risk_names'][name_vi] # Lấy tên đã dịch để hiển thị
        
        with cols[i]:
            st.markdown(f"**{RISK_FILES[name_vi]['icon']} {name_display}**")
            st.markdown("---", unsafe_allow_html=True)

            try:
                threshold_col = [col for col in df.columns if 'Risk_Threshold' in col]
                if not threshold_col:
                    st.error(t("threshold_col_error"))
                    continue
                threshold_col = threshold_col[0]

                risk_row = df.loc[(selected_month, selected_day)]

                threshold_val = risk_row[threshold_col]
                unit = RISK_FILES[name_vi]['unit']
                
                # Lấy chuỗi 'trên'/'dưới' đã dịch
                risk_type_display = t(RISK_FILES[name_vi]['type_key'])

                st.info(f"{t('risk_threshold_label')} ({risk_type_display}): **{threshold_val:.2f}{unit}**")

                historical_prob = risk_row['Historical_Prob_%']
                theoretical_prob = risk_row['Theoretical_Risk_Prob_%']

                delta_str = f"{t('theoretical_label')}: {theoretical_prob:.2f}%"

                st.metric(
                    label=t("historical_prob_label"),
                    value=f"{historical_prob:.2f}%",
                    delta=delta_str,
                    delta_color="off"
                )

            except KeyError:
                st.warning(t("data_not_found"))
            except Exception:
                st.error(t("unknown_error"))

    st.markdown("---")
    st.subheader(t("download_header"))
    st.markdown(t("download_info"))

    cols_dl = st.columns(5)

    for i, name_vi in enumerate(risk_names_vi):
        df = risk_data[name_vi]
        # Lấy tên Tiếng Anh (hoặc Tiếng Việt) để đặt tên file, dùng tên hiển thị trên nút
        name_display = lang['risk_names'][name_vi].split('(')[0].strip()
        
        with cols_dl[i]:
            st.download_button(
                label=f"{t('download_header')} {RISK_FILES[name_vi]['icon']} {name_display} (CSV)",
                data=df.to_csv().encode('utf-8'),
                file_name=f'risk_analysis_{name_vi.split()[0].lower()}.csv',
                mime='text/csv'
            )
