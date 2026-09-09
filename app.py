import os
import shutil

# Thư mục chứa dự án
root = "crm_ngan_hang_streamlit"
if os.path.exists(root):
    shutil.rmtree(root)
os.makedirs(os.path.join(root, ".streamlit"), exist_ok=True)

files = {
    "app.py": r'''
import streamlit as st
from database import init_db, create_loan, list_loans, get_loan, update_status
from ui import loan_form, dashboard, loan_detail

st.set_page_config(page_title="Techcombank · Quản lý hồ sơ vay", page_icon="🏦", layout="wide")
init_db()

st.markdown("""
<style>
.block-container {padding-top: 1.5rem; max-width: 1400px;}
[data-testid="stSidebar"] {min-width: 250px; max-width: 250px;}
.metric-card {padding: 16px; border: 1px solid #e5e7eb; border-radius: 12px;}
.small-muted {color:#6b7280;font-size:.85rem;}
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    # Hiển thị Logo Techcombank
    try:
        st.image("logo.jpg", use_container_width=True)
    except Exception:
        st.caption("⚠️ [Thêm file logo.JPG vào thư mục để hiển thị logo]")

    st.title("🏦 Techcombank")
    st.caption("Hệ thống quản lý hồ sơ cấp khoản vay")
    page = st.radio("Điều hướng", ["Tổng quan", "Hồ sơ vay", "Tiếp nhận hồ sơ", "Tra cứu"])
    st.divider()
    st.caption("Phiên bản demo nội bộ")
    st.warning("Không nhập dữ liệu khách hàng thật vào bản demo này.", icon="⚠️")

if page == "Tổng quan":
    dashboard()
elif page == "Tiếp nhận hồ sơ":
    st.header("Tiếp nhận hồ sơ cấp khoản vay")
    data, files = loan_form()
    if st.button("💾 Lưu hồ sơ", type="primary", use_container_width=True):
        if not data["full_name"] or not data["national_id"] or data["loan_amount"] <= 0:
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
            c1,c2,c3,c4,c5 = st.columns([1.3,2.4,1.5,1.5,1.2])
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
        with st.expander(f'{row["loan_id"]} · {row["full_name"]} · {row["status"]}'):
            st.write(f'CCCD: {row["national_id"]}')
            st.write(f'Số tiền vay: {row["loan_amount"]:,.0f} đ')
            st.write(f'Mục đích: {row["purpose"]}')
''',
    "database.py": r'''
import sqlite3, os, uuid, json
from datetime import datetime

DB = "bank_loan.db"

def conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    with conn() as db:
        db.execute("""
        CREATE TABLE IF NOT EXISTS loans (
            loan_id TEXT PRIMARY KEY,
            full_name TEXT NOT NULL,
            national_id TEXT NOT NULL,
            dob TEXT,
            occupation TEXT,
            income REAL DEFAULT 0,
            purpose TEXT,
            loan_amount REAL DEFAULT 0,
            phone TEXT,
            address TEXT,
            status TEXT DEFAULT 'Mới tiếp nhận',
            documents TEXT DEFAULT '[]',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """)
        db.commit()

def create_loan(data, files):
    now = datetime.now().isoformat(timespec="seconds")
    loan_id = "TCB-" + datetime.now().strftime("%Y%m%d") + "-" + uuid.uuid4().hex[:6].upper()
    with conn() as db:
        db.execute("""INSERT INTO loans
        (loan_id,full_name,national_id,dob,occupation,income,purpose,loan_amount,phone,address,documents,created_at,updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (loan_id, data["full_name"], data["national_id"], str(data["dob"]),
         data["occupation"], data["income"], data["purpose"], data["loan_amount"],
         data["phone"], data["address"], json.dumps(files, ensure_ascii=False), now, now))
        db.commit()
    return loan_id

def list_loans(q=""):
    with conn() as db:
        if q:
            like = f"%{q}%"
            rows = db.execute("""SELECT * FROM loans
                WHERE loan_id LIKE ? OR full_name LIKE ? OR national_id LIKE ?
                ORDER BY created_at DESC""", (like,like,like)).fetchall()
        else:
            rows = db.execute("SELECT * FROM loans ORDER BY created_at DESC").fetchall()
    return [dict(r) for r in rows]

def get_loan(loan_id):
    with conn() as db:
        r = db.execute("SELECT * FROM loans WHERE loan_id=?", (loan_id,)).fetchone()
    return dict(r) if r else None

def update_status(loan_id, status):
    with conn() as db:
        db.execute("UPDATE loans SET status=?, updated_at=? WHERE loan_id=?",
                   (status, datetime.now().isoformat(timespec="seconds"), loan_id))
        db.commit()
''',
    "ui.py": r'''
import streamlit as st
from datetime import date
from database import list_loans, get_loan, update_status
import json

STATUSES = ["Mới tiếp nhận","Đang thẩm định","Bổ sung hồ sơ","Đề xuất phê duyệt","Đã duyệt","Từ chối","Đã giải ngân"]

def loan_form():
    st.subheader("1. Thông tin khách hàng")
    c1,c2 = st.columns(2)
    full_name = c1.text_input("Họ và tên *")
    national_id = c2.text_input("CCCD *")
    c3,c4,c5 = st.columns(3)
    dob = c3.date_input("Ngày tháng năm sinh", value=date(1990,1,1), min_value=date(1900,1,1))
    occupation = c4.text_input("Nghề nghiệp")
    phone = c5.text_input("Số điện thoại")
    address = st.text_area("Địa chỉ", height=80)

    st.subheader("2. Thông tin tài chính & khoản vay")
    c1,c2,c3 = st.columns(3)
    income = c1.number_input("Thu nhập hàng tháng (VNĐ)", min_value=0.0, step=500000.0)
    loan_amount = c2.number_input("Số tiền vay (VNĐ) *", min_value=0.0, step=1000000.0)
    purpose = c3.selectbox("Mục đích vay", ["Mua nhà","Mua ô tô","Kinh doanh","Tiêu dùng","Học tập","Sửa chữa nhà","Khác"])

    st.subheader("3. Tài liệu chứng minh")
    uploads = st.file_uploader(
        "Tải tài liệu (PDF/JPG/PNG/DOCX/XLSX)",
        type=["pdf","jpg","jpeg","png","docx","xlsx"],
        accept_multiple_files=True
    )
    files = [{"name": f.name, "size": f.size, "type": f.type} for f in uploads]
    if files:
        st.caption("Tài liệu đã chọn: " + ", ".join(x["name"] for x in files))

    return {
        "full_name": full_name.strip(),
        "national_id": national_id.strip(),
        "dob": dob,
        "occupation": occupation.strip(),
        "income": income,
        "purpose": purpose,
        "loan_amount": loan_amount,
        "phone": phone.strip(),
        "address": address.strip(),
    }, files

def dashboard():
    st.title("Tổng quan hồ sơ tín dụng Techcombank")
    rows = list_loans()
    total = len(rows)
    pending = sum(r["status"] in ["Mới tiếp nhận","Đang thẩm định","Bổ sung hồ sơ"] for r in rows)
    approved = sum(r["status"] == "Đã duyệt" for r in rows)
    disbursed = sum(r["status"] == "Đã giải ngân" for r in rows)
    requested = sum(r["loan_amount"] or 0 for r in rows)

    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric("Tổng hồ sơ", total)
    c2.metric("Đang xử lý", pending)
    c3.metric("Đã duyệt", approved)
    c4.metric("Đã giải ngân", disbursed)
    c5.metric("Tổng tiền đề nghị", f"{requested/1e9:.2f} tỷ")

    st.divider()
    st.subheader("Hồ sơ gần đây")
    for r in rows[:10]:
        st.write(f'**{r["loan_id"]}** — {r["full_name"]} — {r["loan_amount"]:,.0f} đ — `{r["status"]}`')

def loan_detail(loan_id):
    r = get_loan(loan_id)
    if not r:
        return
    st.subheader(f'Hồ sơ {r["loan_id"]}')
    c1,c2 = st.columns(2)
    with c1:
        st.write(f'**Họ tên:** {r["full_name"]}')
        st.write(f'**CCCD:** {r["national_id"]}')
        st.write(f'**Ngày sinh:** {r["dob"]}')
        st.write(f'**Nghề nghiệp:** {r["occupation"]}')
        st.write(f'**Thu nhập:** {r["income"]:,.0f} đ/tháng')
    with c2:
        st.write(f'**Mục đích vay:** {r["purpose"]}')
        st.write(f'**Số tiền vay:** {r["loan_amount"]:,.0f} đ')
        st.write(f'**Điện thoại:** {r["phone"]}')
        st.write(f'**Địa chỉ:** {r["address"]}')
        st.write(f'**Tạo lúc:** {r["created_at"]}')

    docs = json.loads(r["documents"] or "[]")
    st.write("**Tài liệu chứng minh:**")
    if docs:
        for d in docs: st.write(f'- {d["name"]} ({d["size"]} bytes)')
    else:
        st.caption("Chưa có tài liệu.")

    new_status = st.selectbox("Cập nhật trạng thái", STATUSES, index=STATUSES.index(r["status"]) if r["status"] in STATUSES else 0)
    if st.button("Cập nhật trạng thái", type="primary"):
        update_status(loan_id, new_status)
        st.success("Đã cập nhật.")
        st.rerun()
''',
    "requirements.txt": "streamlit>=1.40\npandas>=2.0\nopenpyxl>=3.1\n",
    ".streamlit/config.toml": """
[theme]
base="light"
primaryColor="#E11B22"
backgroundColor="#FFFFFF"
secondaryBackgroundColor="#F8F9FA"
textColor="#172033"
""",
}

for path, content in files.items():
    file_path = os.path.join(root, path)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content.strip())

print(f"✅ Đã khởi tạo xong dự án tại thư mục '{root}'!")
