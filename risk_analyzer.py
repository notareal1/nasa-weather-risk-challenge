import pandas as pd
import numpy as np
from scipy.stats import norm
import os

START_YEAR = 1980
END_YEAR = 2010
RISK_THRESHOLD = 2.0
RISK_THRESHOLD_COLD = -2.0
SKIP_ROWS = 8

FILE_MAX_TEMP = 'g4.areaAvgTimeSeries.M2SDNXSLV_5_12_4_T2MMAX.19480101-20250926.105E_20N_106E_21N.csv'
FILE_MIN_TEMP = 'g4.areaAvgTimeSeries.M2SDNXSLV_5_12_4_T2MMIN.19480101-20250926.105E_20N_106E_21N.csv'
FILE_MAX_WIND = 'g4.areaAvgTimeSeries.M2T1NXFLX_5_12_4_SPEEDMAX.19480101-20250927.105E_20N_106E_21N.csv'
FILE_WATER_VAPOR = 'g4.areaAvgTimeSeries.MYD08_D3_6_1_Atmospheric_Water_Vapor_QA_Mean.19480101-20250929.105E_20N_106E_21N.csv'
FILE_RAINFALL = 'g4.areaAvgTimeSeries.GLDAS_CLSM025_D_2_0_Rainf_tavg.19480101-20250926.105E_20N_106E_21N.csv'


# 2. ĐỊNH NGHĨA CÁC HÀM XỬ LÝ DỮ LIỆU
def load_and_clean_temp_dew(file_path, skip_rows):
    try:
        df = pd.read_csv(file_path, skiprows=skip_rows, header=0)
        df.columns = ['Date', 'Value_K']
        df['Date'] = pd.to_datetime(df['Date'])
        df['Value_C'] = df['Value_K'] - 273.15
        return df.drop(columns=['Value_K']).rename(columns={'Value_C': 'Value'}) 
    except Exception as e:
        print(f"LỖI ĐỌC FILE KELVIN {file_path}. {e}")
        return None

def load_and_clean_non_temp(file_path, skip_rows, value_col_name):
    try:
        df = pd.read_csv(file_path, skiprows=skip_rows, header=0)
        df.columns = ['Date', value_col_name]
        df['Date'] = pd.to_datetime(df['Date'])
        return df.rename(columns={value_col_name: 'Value'}) 
    except Exception as e:
        print(f"LỖI ĐỌC FILE NON-KELVIN {file_path}. {e}")
        return None

def analyze_risk_stats(df, start_year, end_year, risk_threshold, threshold_col_name):
    df_baseline = df[(df['Date'].dt.year >= start_year) & (df['Date'].dt.year <= end_year)].copy()
    
    baseline_stats = df_baseline.groupby([df_baseline['Date'].dt.month, df_baseline['Date'].dt.day])['Value'].agg(['mean', 'std'])
    baseline_stats.index.names = ['Month', 'Day']
    
    baseline_stats[threshold_col_name] = baseline_stats['mean'] + (baseline_stats['std'] * risk_threshold)
    return baseline_stats

def calculate_historical_probability(df_full, risk_stats, start_year, end_year, risk_type, threshold_col_name):
    df_baseline = df_full[(df_full['Date'].dt.year >= start_year) & (df_full['Date'].dt.year <= end_year)].copy()
    
    df_baseline['Month'] = df_baseline['Date'].dt.month
    df_baseline['Day'] = df_baseline['Date'].dt.day
    
    risk_stats_to_merge = risk_stats[[threshold_col_name]].copy()
    df_baseline = pd.merge(df_baseline, 
                            risk_stats_to_merge, 
                            on=['Month', 'Day'], 
                            how='left')
    
    if risk_type in ['hot', 'wind', 'water_vapor', 'rainfall']:
        df_baseline['Baseline_Risk'] = (df_baseline['Value'] > df_baseline[threshold_col_name]).astype(int)
    elif risk_type == 'cold':
        df_baseline['Baseline_Risk'] = (df_baseline['Value'] < df_baseline[threshold_col_name]).astype(int)

    if df_full['Date'].iloc[1] - df_full['Date'].iloc[0] < pd.Timedelta(hours=24):
        df_baseline['Date_Only'] = df_baseline['Date'].dt.normalize()
        df_baseline = df_baseline.groupby(['Date_Only', 'Month', 'Day'])['Baseline_Risk'].max().reset_index()
        df_baseline = df_baseline[df_baseline['Baseline_Risk'].notna()]

    risk_counts = df_baseline.groupby(['Month', 'Day'])['Baseline_Risk'].sum().reset_index()
    total_days = df_baseline.groupby(['Month', 'Day'])['Baseline_Risk'].count().reset_index(name='Total_Days')
    
    prob_df = pd.merge(risk_counts, total_days, on=['Month', 'Day'])
    prob_df['Historical_Prob_%'] = (prob_df['Baseline_Risk'] / prob_df['Total_Days']) * 100
    
    return prob_df.set_index(['Month', 'Day'])[['Historical_Prob_%']]


# 3. CHẠY CHƯƠNG TRÌNH CHÍNH (MAIN EXECUTION) 

probability_theory = norm.sf(RISK_THRESHOLD) * 100

risk_stats_all = {}

# 1. MAX TEMP (VERY HOT)
df_max = load_and_clean_temp_dew(FILE_MAX_TEMP, SKIP_ROWS)
if df_max is not None:
    risk_stats_max = analyze_risk_stats(df_max, START_YEAR, END_YEAR, RISK_THRESHOLD, 'Risk_Threshold_C')
    prob_hot = calculate_historical_probability(df_max, risk_stats_max, START_YEAR, END_YEAR, 'hot', 'Risk_Threshold_C')
    risk_stats_max = risk_stats_max.join(prob_hot)
    risk_stats_max['Theoretical_Risk_Prob_%'] = probability_theory
    risk_stats_all['risk_stats_max'] = risk_stats_max

# 2. MIN TEMP (VERY COLD)
df_min = load_and_clean_temp_dew(FILE_MIN_TEMP, SKIP_ROWS)
if df_min is not None:
    risk_stats_min = analyze_risk_stats(df_min, START_YEAR, END_YEAR, RISK_THRESHOLD_COLD, 'Risk_Threshold_C')
    prob_cold = calculate_historical_probability(df_min, risk_stats_min, START_YEAR, END_YEAR, 'cold', 'Risk_Threshold_C')
    risk_stats_min = risk_stats_min.join(prob_cold)
    risk_stats_min['Theoretical_Risk_Prob_%'] = probability_theory
    risk_stats_all['risk_stats_min'] = risk_stats_min

# 3. MAX WIND (VERY WINDY)
df_wind = load_and_clean_non_temp(FILE_MAX_WIND, SKIP_ROWS, 'Wind_m_s')
if df_wind is not None:
    risk_stats_wind = analyze_risk_stats(df_wind, START_YEAR, END_YEAR, RISK_THRESHOLD, 'Risk_Threshold_m_s')
    prob_wind = calculate_historical_probability(df_wind, risk_stats_wind, START_YEAR, END_YEAR, 'wind', 'Risk_Threshold_m_s')
    risk_stats_wind = risk_stats_wind.join(prob_wind)
    risk_stats_wind['Theoretical_Risk_Prob_%'] = probability_theory
    risk_stats_all['risk_stats_wind'] = risk_stats_wind

# 4. ATMOSPHERIC WATER VAPOR (VERY HUMID/WET - Cực Đoan)
df_water_vapor = load_and_clean_non_temp(FILE_WATER_VAPOR, SKIP_ROWS, 'Water_Vapor_Total')
if df_water_vapor is not None:
    risk_stats_wv = analyze_risk_stats(df_water_vapor, START_YEAR, END_YEAR, RISK_THRESHOLD, 'Water_Vapor_Risk_Threshold')
    prob_wv = calculate_historical_probability(df_water_vapor, risk_stats_wv, START_YEAR, END_YEAR, 'water_vapor', 'Water_Vapor_Risk_Threshold')
    risk_stats_wv = risk_stats_wv.join(prob_wv)
    risk_stats_wv['Theoretical_Risk_Prob_%'] = probability_theory
    risk_stats_all['risk_stats_wv'] = risk_stats_wv 

# 5. RAINFALL CỰC ĐOAN (VERY WET)
df_rainfall = load_and_clean_non_temp(FILE_RAINFALL, SKIP_ROWS, 'Rainfall_mm')
if df_rainfall is not None:
    risk_stats_rain = analyze_risk_stats(df_rainfall, START_YEAR, END_YEAR, RISK_THRESHOLD, 'Rainfall_Risk_Threshold_mm')
    prob_rain = calculate_historical_probability(df_rainfall, risk_stats_rain, START_YEAR, END_YEAR, 'rainfall', 'Rainfall_Risk_Threshold_mm')
    risk_stats_rain = risk_stats_rain.join(prob_rain)
    risk_stats_rain['Theoretical_Risk_Prob_%'] = probability_theory
    risk_stats_all['risk_stats_rain'] = risk_stats_rain



# 4. XUẤT DỮ LIỆU SANG CSV CHO STREAMLIT VÀ IN TÓM TẮT


if 'risk_stats_max' in risk_stats_all and 'risk_stats_rain' in risk_stats_all:
    print("\n" + "="*70)
    print("PHÂN TÍCH XÁC SUẤT RỦI RO CHO MỌI NGÀY TRONG NĂM")
    print("="*70)
    
    theory_prob_output = risk_stats_all['risk_stats_max'].loc[(7, 1), 'Theoretical_Risk_Prob_%']

    # RỦI RO RẤT NÓNG (MAX TEMP)
    jul_1_max = risk_stats_all['risk_stats_max'].loc[(7, 1)]
    print("\n--- RỦI RO RẤT NÓNG (MAX TEMP > Ngưỡng) ---")
    print(f"Ngưỡng Rất Nóng (2.0 Sigma) cho ngày 01/07: {jul_1_max['Risk_Threshold_C']:.2f} °C")
    print(f"Xác suất LỊCH SỬ ngày 01/07 vượt ngưỡng: {jul_1_max['Historical_Prob_%']:.2f}%")
    print(f"Xác suất LÝ THUYẾT (2.0 Sigma): {theory_prob_output:.2f}%")

    # RỦI RO RAINFALL CỰC ĐOAN
    jul_1_rain = risk_stats_all['risk_stats_rain'].loc[(7, 1)]
    print("\n--- RỦI RO MƯA CỰC ĐOAN (RAINFALL > Ngưỡng) ---")
    print(f"Ngưỡng Mưa Khí Quyển cho ngày 01/07: {jul_1_rain['Rainfall_Risk_Threshold_mm']:.2f} mm")
    print(f"Xác suất LỊCH SỬ ngày 01/07 vượt ngưỡng: {jul_1_rain['Historical_Prob_%']:.2f}%")
    print(f"Xác suất LÝ THUYẾT (2.0 Sigma): {theory_prob_output:.2f}%")


print("\n" + "="*70)
print("XUẤT DỮ LIỆU SANG CSV CHO STREAMLIT")
print("="*70)

EXPORT_FILES = {
    'risk_stats_max': 'risk_stats_max.csv',
    'risk_stats_min': 'risk_stats_min.csv',
    'risk_stats_wind': 'risk_stats_wind.csv',
    'risk_stats_wv': 'risk_stats_water_vapor.csv', 
    'risk_stats_rain': 'risk_stats_rainfall.csv',
}

for var_name, file_name in EXPORT_FILES.items():
    if var_name in risk_stats_all:
        try:
            risk_stats_all[var_name].to_csv(file_name)
            print(f"-> Đã xuất thành công: {file_name}")
        except Exception as e:
            print(f"LỖI XUẤT CSV {file_name}: {e}")
    else:
        print(f"BỎ QUA: {var_name} không được tính toán (lỗi tải dữ liệu).")