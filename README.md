# nasa-weather-risk-challenge
Ứng dụng phân tích rủi ro khí hậu cho NASA Space Apps Challenge
Ưu Điểm:

1)Sử dụng xác suất Lịch sử	Dữ liệu NASA thực tế (1980-2010).	Tần suất thực tế mà sự kiện cực đoan xảy ra trong khu vực của Hà Nội.

2)Ngưỡng Rủi ro	Thống kê 2.0 Sigma (2σ)	Bất kỳ giá trị nào vượt quá 2.0 lần Độ lệch chuẩn của lịch sử (nghĩa là nằm trong  ≈2.28% dữ liệu).

3)Xác suất Lý thuyết	Mô hình Phân phối Chuẩn (2.28%).Xác suất xảy ra sự kiện 2σ nếu khí hậu hoàn toàn bình thường, ổn định.

Nguồn Dữ liệu và Công cụ:

Hỗ trợ Lập trình và Logic Phân tích: Gemini.

Công cụ Truy vấn Dữ liệu: NASA Giovanni.

Nguồn Dữ liệu Gốc: NASA GES DISC ,thông qua giao thức OPeNDAP server.

Nhược điểm:

hiện tại là dự án bị giới hạn bởi các file CSV đã có và thời gian cho cuộc thi này. Việc tích hợp API sẽ là bước ngoặt biến nó thành công cụ phân tích rủi ro khí hậu linh hoạt cho mọi vị trí và trong tương lai.

URL Ứng dụng Web: liên kết Streamlit Cloud công khai

https://nasa-weather-risk-challenge-jv5y8qvhmrjcdtbsj5ecvl.streamlit.app/
