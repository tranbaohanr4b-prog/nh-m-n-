import streamlit as st
import pandas as pd
from io import BytesIO

# ==========================================
# CẤU HÌNH TRANG & THƯƠNG HIỆU TECHCOMBANK
# ==========================================
st.set_page_config(
    page_title="Techcombank - Cổng Đăng Ký & Tư Vấn Khoản Vay",
    page_icon="🏦",
    layout="wide"
)

# Đường link Logo chính thức của Techcombank
LOGO_URL = "https://upload.wikimedia.org/wikipedia/commons/7/7c/Techcombank_logo.png"

# Hiển thị Logo trên Sidebar và Trang chính
st.sidebar.image(LOGO_URL, width=200)
st.image(LOGO_URL, width=220)

# ==========================================
# KHỞI TẠO DỮ LIỆU (SESSION STATE)
# ==========================================
if "customers" not in st.session_state:
    st.session_state.customers = []

if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False

# ==========================================
# HÀM XUẤT EXCEL & TÍNH LÃI VAY
# ==========================================
def export_excel():
    df = pd.DataFrame(st.session_state.customers)
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Khách hàng Techcombank")
    return output.getvalue()

def calculate_loan(amount_vnd, rate_year, term_months):
    """Tính lịch trả nợ theo dư nợ giảm dần"""
    monthly_rate = (rate_year / 100) / 12
    principal_monthly = amount_vnd / term_months
    
    schedule = []
    remaining = amount_vnd
    
    for i in range(1, term_months + 1):
        interest_monthly = remaining * monthly_rate
        total_monthly = principal_monthly + interest_monthly
        remaining -= principal_monthly
        schedule.append({
            "Kỳ thứ": i,
            "Gốc trả (VNĐ)": round(principal_monthly),
            "Lãi trả (VNĐ)": round(interest_monthly),
            "Tổng trả/tháng (VNĐ)": round(total_monthly),
            "Dư nợ còn lại (VNĐ)": max(0, round(remaining))
        })
    return pd.DataFrame(schedule)

# ==========================================
# THANH ĐIỀU HƯỚNG (SIDEBAR)
# ==========================================
st.sidebar.title("🏦 TECHCOMBANK CRM")
page = st.sidebar.radio(
    "Chọn dịch vụ:",
    [
        "📊 Tính toán & Tư vấn khoản vay",
        "📝 Đăng ký nhu cầu vay",
        "🔐 Quản trị viên (Admin)"
    ]
)

st.sidebar.divider()
st.sidebar.caption("Ngân hàng TMCP Kỹ thương Việt Nam (Techcombank)")
st.sidebar.info("💡 **Hotline hỗ trợ:** 1800 588 822")

# ==========================================
# TRANG 1: TÍNH TOÁN & TƯ VẤN KHOẢN VAY
# ==========================================
if page == "📊 Tính toán & Tư vấn khoản vay":
    st.title("📊 Công Cụ Tính Toán Khoản Vay Techcombank_NHÓM NỮ")
    st.caption("Ước tính lịch trả nợ và hạn mức thanh toán hàng tháng giúp bạn chủ động kế hoạch tài chính.")
    st.divider()

    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.subheader("⚙️ Thông số khoản vay")
        amount = st.number_input("Số tiền cần vay (VNĐ):", min_value=10_000_000, value=100_000_000, step=10_000_000, format="%d")
        interest_rate = st.number_input("Lãi suất ưu đãi (%/năm):", min_value=1.0, max_value=25.0, value=8.5, step=0.1)
        term = st.slider("Thời hạn vay (tháng):", min_value=3, max_value=120, value=12, step=3)

        st.caption(f"👉 **Số tiền vay:** {amount:,.0f} VNĐ")
        st.caption(f"👉 **Lãi suất:** {interest_rate}%/năm | **Kỳ hạn:** {term} tháng")

    with col2:
        st.subheader("📈 Kết quả ước tính (Dư nợ giảm dần)")
        df_schedule = calculate_loan(amount, interest_rate, term)
        
        first_month = df_schedule.iloc[0]["Tổng trả/tháng (VNĐ)"]
        total_interest = df_schedule["Lãi trả (VNĐ)"].sum()
        total_payment = amount + total_interest

        m1, m2 = st.columns(2)
        m1.metric("Tháng đầu trả khoảng", f"{first_month:,.0f} đ")
        m2.metric("Tổng lãi phải trả", f"{total_interest:,.0f} đ")

        st.metric("Tổng gốc + Lãi cả kỳ", f"{total_payment:,.0f} đ")

    st.divider()
    with st.expander("🔍 Xem bảng lịch trả nợ chi tiết theo từng tháng"):
        st.dataframe(df_schedule, use_container_width=True, hide_index=True)

# ==========================================
# TRANG 2: ĐĂNG KÝ NHU CẦU VAY
# ==========================================
elif page == "📝 Đăng ký nhu cầu vay":
    st.title("📝 Đăng Ký Tư Vấn Khoản Vay")
    st.write("Vui lòng để lại thông tin, Cán bộ Tín dụng Techcombank sẽ liên hệ hỗ trợ bạn trong thời gian sớm nhất.")
    st.divider()

    with st.form("loan_registration_form", clear_on_submit=True):
        st.subheader("1. Thông tin cá nhân")
        c1, c2 = st.columns(2)
        name = c1.text_input("Họ và tên *", placeholder="Ví dụ: Nguyễn Văn A")
        phone = c2.text_input("Số điện thoại liên hệ *", placeholder="Ví dụ: 0912345678")

        address = st.text_input("Địa chỉ hiện tại", placeholder="Số nhà, đường, quận/huyện, tỉnh/thành phố")

        st.subheader("2. Thông tin nhu cầu tín dụng")
        c3, c4 = st.columns(2)
        loan_amount_req = c3.number_input("Số tiền đề nghị vay (VNĐ) *", min_value=5_000_000, value=50_000_000, step=5_000_000, format="%d")
        loan_purpose = c4.selectbox(
            "Mục đích vay *",
            ["Vay mua nhà / Sửa nhà", "Vay mua ô tô", "Vay tiêu dùng linh hoạt", "Vay bổ sung vốn kinh doanh", "Khác"]
        )

        income = st.text_input("Thu nhập bình quân/tháng (Không bắt buộc)", placeholder="Ví dụ: 15 triệu")
        note = st.text_area("Ghi chú bổ sung", placeholder="Khung giờ có thể nghe máy, tài sản đảm bảo...")

        submit_btn = st.form_submit_button("🚀 GỬI ĐĂNG KÝ VAY TECHCOMBANK", type="primary", use_container_width=True)

    if submit_btn:
        if not name.strip():
            st.error("❌ Vui lòng nhập Họ và tên.")
        elif not phone.strip():
            st.error("❌ Vui lòng nhập Số điện thoại.")
        else:
            customer_record = {
                "Họ và tên": name.strip(),
                "Số điện thoại": phone.strip(),
                "Số tiền vay đề nghị": f"{loan_amount_req:,.0f} VNĐ",
                "Mục đích vay": loan_purpose,
                "Thu nhập/tháng": income.strip() if income else "Chưa cung cấp",
                "Địa chỉ": address.strip() if address else "Chưa cung cấp",
                "Ghi chú": note.strip() if note else "Không",
            }
            st.session_state.customers.append(customer_record)
            st.success("✅ Đã gửi thông tin đăng ký thành công! Chuyên viên tư vấn Techcombank sẽ liên hệ sớm nhất.")

# ==========================================
# TRANG 3: QUẢN TRỊ VIÊN (ADMIN)
# ==========================================
elif page == "🔐 Quản trị viên (Admin)":
    st.title("🔐 Hệ Thống Quản Trị Hồ Sơ Tín Dụng")
    st.divider()

    if not st.session_state.admin_logged_in:
        col1, col2, col3 = st.columns([1, 1.5, 1])
        with col2:
            st.subheader("🔑 Đăng nhập nội bộ")
            password = st.text_input("Mật khẩu truy cập:", type="password")
            if st.button("ĐĂNG NHẬP", type="primary", use_container_width=True):
                if password == "123456":
                    st.session_state.admin_logged_in = True
                    st.rerun()
                else:
                    st.error("❌ Mật khẩu không chính xác.")
    else:
        top_col1, top_col2 = st.columns([4, 1])
        with top_col1:
            st.subheader("📑 DANH SÁCH KHÁCH HÀNG ĐĂNG KÝ VAY")
        with top_col2:
            if st.button("🚪 Đăng xuất", use_container_width=True):
                st.session_state.admin_logged_in = False
                st.rerun()

        st.divider()

        if len(st.session_state.customers) == 0:
            st.info("📭 Hiện chưa có đăng ký nhu cầu vay nào.")
        else:
            df = pd.DataFrame(st.session_state.customers)

            # Chỉ số nhanh
            m1, m2 = st.columns(2)
            m1.metric("Tổng số khách hàng đăng ký", len(df))
            m2.metric("Trạng thái hệ thống", "Sẵn sàng")

            st.divider()

            # Hiển thị bảng
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.divider()

            # Tải về Excel
            excel_file = export_excel()
            st.download_button(
                label="📥 XUẤT BÁO CÁO EXCEL (.XLSX)",
                data=excel_file,
                file_name="techcombank_danh_sach_vay.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
