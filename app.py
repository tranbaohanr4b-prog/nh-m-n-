import json
import os
import pathlib
import shutil
import textwrap
import zipfile

import streamlit as st
from database import create_loan, get_loan, init_db, list_loans, update_status
from ui import dashboard, loan_detail, loan_form

st.set_page_config(
    page_title="Techcombank · Quản lý hồ sơ vay", page_icon="🏦", layout="wide"
)
init_db()

st.markdown(
    """
<style>
.block-container {padding-top: 1.5rem; max-width: 1400px;}
[data-testid="stSidebar"] {min-width: 260px; max-width: 260px;}
.metric-card {padding: 16px; border: 1px solid #e5e7eb; border-radius: 12px;}
.small-muted {color:#6b7280;font-size:.85rem;}
</style>
""",
    unsafe_allow_html=True,
)

with st.sidebar:
    # --- HIỂN THỊ LOGO TECHCOMBANK ---
    try:
        st.image("logo.JPG", use_container_width=True)
    except Exception:
        st.caption("⚠️ [Thiếu file logo.JPG]")

    st.title("Techcombank")
    st.caption("Hệ thống quản lý hồ sơ cấp khoản vay")
    page = st.radio(
        "Điều hướng", ["Tổng quan", "Hồ sơ vay", "Tiếp nhận hồ sơ", "Tra cứu"]
    )
    st.divider()
    st.caption("Phiên bản demo nội bộ")
    st.warning("Không nhập dữ liệu khách hàng thật vào bản demo này.", icon="⚠️")

if page == "Tổng quan":
    dashboard()
elif page == "Tiếp nhận hồ sơ":
    st.header("Tiếp nhận hồ sơ cấp khoản vay")
    data, files = loan_form()
    if st.button("💾 Lưu hồ sơ", type="primary", use_container_width=True):
        if (
            not data["full_name"]
            or not data["national_id"]
            or data["loan_amount"] <= 0
        ):
            st.error("Vui lòng nhập Họ tên, CCCD và Số tiền vay.")
        else:
            loan_id = create_loan(data, files)
            st.success(f"Đã tạo hồ sơ {loan_id}.")
elif page == "Hồ sơ vay":
    st.header("Quản lý hồ sơ vay")
    loans = list_loans()
    if not loans:
        st.info("Chưa có hồ sơ.")
    else:
        for row in loans:
            c1, c2, c3, c4, c5 = st.columns([1.3, 2.4, 1.5, 1.5, 1.2])
            c1.write(row["loan_id"])
            c2.write(row["full_name"])
            c3.write(f'{row["loan_amount"]:,.0f} đ')
            c4.write(row["status"])
            if c5.button("Xem", key=f"view_{row['loan_id']}"):
                st.session_state["selected_loan"] = row["loan_id"]
        if st.session_state.get("selected_loan"):
            st.divider()
            loan_detail(st.session_state["selected_loan"])
elif page == "Tra cứu":
    st.header("Tra cứu hồ sơ")
    q = st.text_input("Tìm theo mã hồ sơ, họ tên hoặc CCCD")
    rows = list_loans(q)
    for row in rows:
        with st.expander(
            f'{row["loan_id"]} · {row["full_name"]} · {row["status"]}'
        ):
            st.write(f'CCCD: {row["national_id"]}')
            st.write(f'Số tiền vay: {row["loan_amount"]:,.0f} đ')
            st.write(f'Mục đích: {row["purpose"]}')
