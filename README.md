# Demo Streamlit – Nhóm 03

## Chạy thử trên máy tính
1. Cài Python.
2. Mở Terminal/CMD tại thư mục dự án.
3. Chạy: `pip install -r requirements.txt`
4. Chạy: `streamlit run app.py`

## Đưa lên Streamlit Community Cloud
1. Tạo tài khoản GitHub và đăng nhập Streamlit Community Cloud.
2. Tải các file trong thư mục này lên một repository GitHub.
3. Vào https://share.streamlit.io/ → Create app.
4. Chọn repository, branch `main`, file `app.py` → Deploy.

## CSV tùy chọn
CSV cần có:
- `date`: ngày, ví dụ 2026-01-01
- `sales`: số lượng bán
- `item_id` (không bắt buộc): mã SKU, ví dụ FOODS_3_090

Nếu có `item_id`, ứng dụng lọc theo SKU đang chọn. Dữ liệu không có `item_id` sẽ được dùng như chuỗi của SKU hiện tại.

## Lưu ý học thuật
Khi chưa tải dữ liệu, app dùng chuỗi mô phỏng. Dự báo là baseline trung bình theo thứ trong tuần, không phải mô hình ML/LSTM đã huấn luyện. Tồn kho, thời gian giao hàng và tồn kho an toàn là tham số giả định do người dùng nhập. Không trình bày kết quả mô phỏng như kết quả thực nghiệm của Walmart/M5.
