import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import timedelta

st.set_page_config(page_title="Demand & Inventory | Nhóm 03", page_icon="📦", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 1.6rem; padding-bottom: 2rem;}
h1, h2, h3 {letter-spacing: -0.4px;}
[data-testid="stMetric"] {background: #f4f7fb; border: 1px solid #e5eaf2; padding: 14px; border-radius: 12px;}
.small-note {color:#64748b;font-size:0.88rem;}
</style>
""", unsafe_allow_html=True)

st.title("📦 Dự báo nhu cầu & hỗ trợ quản lý tồn kho")
st.caption("ĐỀ TÀI 13 · ỨNG DỤNG AI TRONG DỰ BÁO NHU CẦU HÀNG HÓA · NHÓM 03")

with st.sidebar:
    st.header("⚙️ Thiết lập mô phỏng")
    sku = st.selectbox("Mã sản phẩm (SKU)", ["FOODS_3_090", "FOODS_3_586", "FOODS_3_252"])
    horizon = st.select_slider("Kỳ dự báo", options=[7, 14, 28], value=14, format_func=lambda x: f"{x} ngày")
    stock = st.number_input("Tồn kho hiện tại (đơn vị)", min_value=0, value=420, step=10)
    lead_time = st.number_input("Thời gian giao hàng (ngày)", min_value=1, max_value=60, value=5)
    safety_days = st.number_input("Tồn kho an toàn (số ngày nhu cầu)", min_value=0, max_value=30, value=3)
    st.divider()
    uploaded = st.file_uploader("Tải dữ liệu bán hàng CSV (không bắt buộc)", type=["csv"])
    st.caption("CSV cần có 2 cột: date và sales. Có thể thêm cột item_id để lọc SKU.")

# Reproducible illustrative data. Explicitly labelled as simulated, not M5 daily observations.
seed_map = {"FOODS_3_090": 11, "FOODS_3_586": 22, "FOODS_3_252": 33}
rng = np.random.default_rng(seed_map[sku])
dates = pd.date_range(end=pd.Timestamp.today().normalize() - pd.Timedelta(days=1), periods=84, freq="D")
base_level = {"FOODS_3_090": 13.0, "FOODS_3_586": 9.0, "FOODS_3_252": 7.0}[sku]
weekly = np.array([0.88, 0.82, 0.90, 0.96, 1.04, 1.22, 1.18])
vals = []
for i, d in enumerate(dates):
    trend = 1 + 0.0008 * i
    vals.append(max(0, round(base_level * weekly[d.dayofweek] * trend + rng.normal(0, 1.8))))
history = pd.DataFrame({"date": dates, "sales": vals})

data_source = "DỮ LIỆU MÔ PHỎNG"
if uploaded is not None:
    try:
        raw = pd.read_csv(uploaded)
        raw.columns = [c.strip().lower() for c in raw.columns]
        if not {"date", "sales"}.issubset(raw.columns):
            st.error("CSV chưa đúng cấu trúc. Cần tối thiểu hai cột: date và sales.")
            st.stop()
        if "item_id" in raw.columns:
            raw = raw[raw["item_id"].astype(str) == sku]
        raw["date"] = pd.to_datetime(raw["date"], errors="coerce")
        raw["sales"] = pd.to_numeric(raw["sales"], errors="coerce")
        history = raw.dropna(subset=["date", "sales"]).groupby("date", as_index=False)["sales"].sum().sort_values("date")
        if history.empty:
            st.error("Không tìm thấy dữ liệu hợp lệ cho SKU đã chọn.")
            st.stop()
        data_source = "DỮ LIỆU CSV DO NGƯỜI DÙNG TẢI LÊN"
    except Exception as e:
        st.error(f"Không đọc được CSV: {e}")
        st.stop()

# Transparent baseline: average sales by weekday over the most recent 8 observations of that weekday.
hist = history.copy().sort_values("date")
hist["weekday"] = hist["date"].dt.dayofweek
overall_avg = float(hist.tail(28)["sales"].mean())
weekday_avg = hist.groupby("weekday")["sales"].apply(lambda x: x.tail(8).mean()).to_dict()
future_dates = pd.date_range(hist["date"].max() + pd.Timedelta(days=1), periods=horizon, freq="D")
forecast_vals = [max(0, float(weekday_avg.get(d.dayofweek, overall_avg))) for d in future_dates]
forecast = pd.DataFrame({"date": future_dates, "forecast": forecast_vals})
avg_daily = float(forecast["forecast"].mean())
demand_lt = float(forecast.loc[forecast["date"] <= hist["date"].max() + pd.Timedelta(days=lead_time), "forecast"].sum())
safety_stock = avg_daily * safety_days
target_stock = demand_lt + safety_stock
suggested_order = max(0, int(np.ceil(target_stock - stock)))
risk = "Có nguy cơ thiếu hàng" if stock < demand_lt else ("Cần theo dõi" if stock < target_stock else "Mức tồn kho đang đáp ứng giả định")

st.info(f"Nguồn dữ liệu đang dùng: **{data_source}**. Phương pháp dự báo: baseline mùa vụ theo thứ trong tuần, không phải mô hình ML/LSTM đã huấn luyện.")

m1, m2, m3, m4 = st.columns(4)
m1.metric("Nhu cầu TB dự báo/ngày", f"{avg_daily:.1f}")
m2.metric(f"Nhu cầu trong {lead_time} ngày giao", f"{demand_lt:,.0f}")
m3.metric("Tồn kho an toàn giả định", f"{safety_stock:,.0f}")
m4.metric("Lượng bổ sung tham khảo", f"{suggested_order:,.0f} đơn vị")

if stock < demand_lt:
    st.error(f"⚠️ {risk}: tồn kho hiện tại thấp hơn nhu cầu dự kiến trong thời gian giao hàng.")
elif stock < target_stock:
    st.warning(f"🟠 {risk}: tồn kho đủ cho nhu cầu giao hàng theo ước tính nhưng thấp hơn ngưỡng mục tiêu.")
else:
    st.success(f"🟢 {risk}.")

left, right = st.columns([1.65, 1])
with left:
    st.subheader("📈 Nhu cầu lịch sử và dự báo")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=hist["date"], y=hist["sales"], mode="lines", name="Doanh số lịch sử", line=dict(width=2)))
    fig.add_trace(go.Scatter(x=forecast["date"], y=forecast["forecast"], mode="lines+markers", name="Dự báo baseline", line=dict(width=3, dash="dash")))
    fig.update_layout(height=390, margin=dict(l=10,r=10,t=25,b=10), xaxis_title="", yaxis_title="Số lượng bán", legend=dict(orientation="h", y=1.12))
    st.plotly_chart(fig, use_container_width=True)
with right:
    st.subheader("🧭 Chỉ báo quản lý")
    st.write(f"**SKU:** `{sku}`")
    st.write(f"**Tồn kho hiện tại:** {stock:,.0f} đơn vị")
    st.write(f"**Thời gian giao hàng:** {lead_time} ngày")
    st.write(f"**Ngưỡng tồn kho mục tiêu:** {target_stock:,.0f} đơn vị")
    st.write(f"**Kỳ dự báo hiển thị:** {horizon} ngày")
    st.caption("Lượng bổ sung chỉ là tham khảo theo giả định đơn giản; chưa tính đơn hàng đang về, MOQ, chi phí đặt hàng, hạn sử dụng và mức dịch vụ.")

st.subheader("🗓️ Bảng dự báo theo ngày")
show = forecast.copy()
show["date"] = show["date"].dt.strftime("%d/%m/%Y")
show["forecast"] = show["forecast"].round(1)
st.dataframe(show.rename(columns={"date":"Ngày", "forecast":"Nhu cầu dự báo (đơn vị)"}), use_container_width=True, hide_index=True)

with st.expander("📚 Cách tính và giới hạn của prototype"):
    st.markdown("""
    **Cách tính minh họa**
    1. Lấy tối đa 8 quan sát gần nhất của từng thứ trong tuần.
    2. Dùng trung bình theo thứ trong tuần làm dự báo baseline.
    3. Nhu cầu trong thời gian giao hàng = tổng dự báo từ ngày kế tiếp đến hết thời gian giao hàng.
    4. Tồn kho an toàn = nhu cầu dự báo trung bình/ngày × số ngày an toàn do người dùng chọn.
    5. Lượng bổ sung tham khảo = max(0, nhu cầu giao hàng + tồn kho an toàn − tồn kho hiện tại).

    **Giới hạn**
    - Khi chưa tải CSV, dữ liệu biểu đồ là dữ liệu mô phỏng để minh họa giao diện, không phải chuỗi bán hàng gốc của Walmart/M5.
    - Baseline không phải mô hình AI đã huấn luyện và chưa có đánh giá sai số trên tập kiểm thử.
    - M5 không cung cấp tồn kho thực tế và thời gian giao hàng; các thông số này do người trình diễn nhập để mô phỏng quyết định.
    - Doanh số bằng 0 không nhất thiết đồng nghĩa nhu cầu bằng 0; có thể chịu ảnh hưởng của tình trạng hết hàng.
    """)

st.divider()
st.caption("NHÓM 03 · Prototype phục vụ minh họa học thuật · Không sử dụng để ra quyết định nhập hàng thực tế.")
