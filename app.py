import sqlite3
import pandas as pd
import plotly.express as px
import streamlit as st
from datetime import datetime, date

# ==========================================
# 1. CẤU HÌNH TRANG VÀ CSS (GIAO DIỆN CHUYÊN NGHIỆP)
# ==========================================
st.set_page_config(
    page_title="Hệ Thống Quản Lý Khách Sạn - HMS Pro",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS cho thẻ trạng thái phòng và tổng quan
st.markdown("""
    <style>
    .main { padding: 1.5rem; }
    .stMetric {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #e9ecef;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .room-card {
        padding: 18px;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .room-card h3 { margin: 0 0 8px 0; color: white; font-size: 22px; }
    .room-card p { margin: 3px 0; font-size: 14px; }
    .status-trong { background: linear-gradient(135deg, #28a745, #20c997); }
    .status-dang-o { background: linear-gradient(135deg, #dc3545, #f8d7da); color: #721c24 !important; }
    .status-dang-o h3 { color: #721c24 !important; }
    .status-dat-truoc { background: linear-gradient(135deg, #ffc107, #ffe8a1); color: #856404 !important; }
    .status-dat-truoc h3 { color: #856404 !important; }
    .status-bao-tri { background: linear-gradient(135deg, #6c757d, #adb5bd); }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. XỬ LÝ CƠ SỞ DỮ LIỆU (SQLITE)
# ==========================================
DB_FILE = "hotel_management.db"

def get_connection():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    
    # Bảng danh sách phòng
    c.execute('''
        CREATE TABLE IF NOT EXISTS rooms (
            room_number TEXT PRIMARY KEY,
            room_type TEXT NOT NULL,
            price REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'Trống'
        )
    ''')
    
    # Bảng lưu lịch sử đặt phòng & hóa đơn
    c.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_number TEXT NOT NULL,
            customer_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            check_in DATE NOT NULL,
            check_out DATE NOT NULL,
            total_price REAL NOT NULL,
            booking_status TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (room_number) REFERENCES rooms (room_number)
        )
    ''')
    
    # Khởi tạo dữ liệu mẫu nếu chưa có phòng nào
    c.execute("SELECT COUNT(*) FROM rooms")
    if c.fetchone()[0] == 0:
        sample_rooms = [
            ('101', 'Đơn (Standard)', 500000, 'Trống'),
            ('102', 'Đơn (Standard)', 500000, 'Đang ở'),
            ('201', 'Đôi (VIP)', 800000, 'Trống'),
            ('202', 'Đôi (VIP)', 800000, 'Đặt trước'),
            ('301', 'Gia đình (Suite)', 1200000, 'Bảo trì'),
            ('302', 'Gia đình (Suite)', 1200000, 'Trống')
        ]
        c.executemany("INSERT INTO rooms VALUES (?, ?, ?, ?)", sample_rooms)
        
        # Booking mẫu cho phòng 102
        c.execute('''
            INSERT INTO bookings (room_number, customer_name, phone, check_in, check_out, total_price, booking_status)
            VALUES ('102', 'Nguyễn Văn A', '0901234567', ?, ?, 500000, 'Đã nhận phòng')
        ''', (date.today().strftime('%Y-%m-%d'), date.today().strftime('%Y-%m-%d')))
        
    conn.commit()
    conn.close()

init_db()

# ==========================================
# 3. CÁC HÀM TRUY VẤN VÀ CẬP NHẬT
# ==========================================
def load_rooms():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM rooms ORDER BY room_number ASC", conn)
    conn.close()
    return df

def update_room_status(room_number, new_status):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE rooms SET status = ? WHERE room_number = ?", (new_status, room_number))
    conn.commit()
    conn.close()

def create_booking(room_number, customer_name, phone, check_in, check_out, total_price):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO bookings (room_number, customer_name, phone, check_in, check_out, total_price, booking_status)
        VALUES (?, ?, ?, ?, ?, ?, 'Đã nhận phòng')
    ''', (room_number, customer_name, phone, check_in, check_out, total_price))
    c.execute("UPDATE rooms SET status = 'Đang ở' WHERE room_number = ?", (room_number,))
    conn.commit()
    conn.close()

def checkout_room(room_number):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE rooms SET status = 'Trống' WHERE room_number = ?", (room_number,))
    c.execute("UPDATE bookings SET booking_status = 'Đã trả phòng' WHERE room_number = ? AND booking_status = 'Đã nhận phòng'", (room_number,))
    conn.commit()
    conn.close()

def delete_room(room_number):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM rooms WHERE room_number = ?", (room_number,))
    conn.commit()
    conn.close()

# ==========================================
# 4. THANH ĐIỀU HƯỚNG (SIDEBAR)
# ==========================================
st.sidebar.title("🏨 HMS NAVIGATOR")
st.sidebar.markdown("---")

menu = st.sidebar.radio(
    "CHỨC NĂNG CHÍNH",
    ["📌 Sơ đồ phòng Live", "🔑 Nhận & Trả phòng", "⚙️ Quản lý danh mục phòng", "📊 Báo cáo doanh thu"]
)

st.sidebar.markdown("---")
st.sidebar.info("💡 **Mẹo:** Dùng trang **Sơ đồ phòng** để theo dõi nhanh trạng thái khách sạn thời gian thực.")

# ------------------------------------------
# CHỨC NĂNG 1: SƠ ĐỒ PHÒNG LIVE
# ------------------------------------------
if menu == "📌 Sơ đồ phòng Live":
    st.title("📌 Sơ Đồ Phòng Theo Thời Gian Thực")
    
    df_rooms = load_rooms()
    
    # Chỉ số nhanh (Metrics)
    total_r = len(df_rooms)
    occupied_r = len(df_rooms[df_rooms['status'] == 'Đang ở'])
    available_r = len(df_rooms[df_rooms['status'] == 'Trống'])
    reserved_r = len(df_rooms[df_rooms['status'] == 'Đặt trước'])
    maint_r = len(df_rooms[df_rooms['status'] == 'Bảo trì'])
    
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Tổng số phòng", total_r)
    c2.metric("Đang có khách", occupied_r, delta=f"{(occupied_r/total_r)*100 if total_r > 0 else 0:.0f}% công suất")
    c3.metric("Phòng trống", available_r)
    c4.metric("Đặt trước", reserved_r)
    c5.metric("Bảo trì", maint_r)
    
    st.markdown("---")
    
    # Lọc trạng thái
    filter_status = st.multiselect(
        "Lọc hiển thị theo trạng thái:",
        options=["Trống", "Đang ở", "Đặt trước", "Bảo trì"],
        default=["Trống", "Đang ở", "Đặt trước", "Bảo trì"]
    )
    
    filtered_rooms = df_rooms[df_rooms['status'].isin(filter_status)]
    
    if filtered_rooms.empty:
        st.warning("Không tìm thấy phòng phù hợp với bộ lọc!")
    else:
        # Render Grid 4 Cột
        cols = st.columns(4)
        status_class = {
            "Trống": "status-trong",
            "Đang ở": "status-dang-o",
            "Đặt trước": "status-dat-truoc",
            "Bảo trì": "status-bao-tri"
        }
        
        for idx, row in filtered_rooms.reset_index(drop=True).iterrows():
            col_idx = idx % 4
            css_cls = status_class.get(row['status'], "")
            with cols[col_idx]:
                st.markdown(
                    f"""
                    <div class="room-card {css_cls}">
                        <h3>Phòng {row['room_number']}</h3>
                        <p><b>Loại:</b> {row['room_type']}</p>
                        <p><b>Trạng thái:</b> {row['status']}</p>
                        <p><b>Giá:</b> {row['price']:,.0f} VNĐ/đêm</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

# ------------------------------------------
# CHỨC NĂNG 2: NHẬN PHÒNG & TRẢ PHÒNG
# ------------------------------------------
elif menu == "🔑 Nhận & Trả phòng":
    st.title("🔑 Lễ Tân - Nhận & Trả Phòng")
    
    tab1, tab2 = st.tabs(["📝 Check-in (Nhận phòng)", "💳 Check-out (Trả phòng)"])
    df_rooms = load_rooms()
    
    # --- TAB CHECK-IN ---
    with tab1:
        st.subheader("Đăng ký nhận phòng mới")
        available_rooms = df_rooms[df_rooms['status'] == 'Trống']
        
        if available_rooms.empty:
            st.error("Rất tiếc! Hiện tại khách sạn không còn phòng trống.")
        else:
            with st.form("form_checkin"):
                col_a, col_b = st.columns(2)
                
                with col_a:
                    selected_room = st.selectbox("Chọn số phòng", available_rooms['room_number'].tolist())
                    customer_name = st.text_input("Họ và tên khách hàng (*)")
                    phone = st.text_input("Số điện thoại / CCCD (*)")
                
                with col_b:
                    check_in_date = st.date_input("Ngày nhận phòng", date.today())
                    check_out_date = st.date_input("Ngày trả phòng dự kiến", date.today())
                    
                    room_info = available_rooms[available_rooms['room_number'] == selected_room].iloc[0]
                    days = max((check_out_date - check_in_date).days, 1)
                    est_price = days * room_info['price']
                    
                    st.markdown(f"**Loại phòng:** {room_info['room_type']}")
                    st.markdown(f"**Số đêm ở:** {days} đêm")
                    st.success(f"**Tổng tiền dự tính:** {est_price:,.0f} VNĐ")
                
                btn_checkin = st.form_submit_button("Xác nhận Check-in")
                if btn_checkin:
                    if not customer_name.strip() or not phone.strip():
                        st.error("Vui lòng nhập đầy đủ Tên và Số điện thoại khách hàng!")
                    else:
                        create_booking(selected_room, customer_name, phone, check_in_date, check_out_date, est_price)
                        st.success(f"Tạo thành công lượt ở cho Phòng {selected_room}!")
                        st.rerun()

    # --- TAB CHECK-OUT ---
    with tab2:
        st.subheader("Thanh toán & Trả phòng")
        occupied_rooms = df_rooms[df_rooms['status'] == 'Đang ở']
        
        if occupied_rooms.empty:
            st.info("Hiện không có phòng nào đang có khách ở.")
        else:
            selected_out_room = st.selectbox("Chọn phòng cần trả", occupied_rooms['room_number'].tolist())
            
            conn = get_connection()
            booking_info = pd.read_sql('''
                SELECT * FROM bookings 
                WHERE room_number = ? AND booking_status = 'Đã nhận phòng'
                ORDER BY id DESC LIMIT 1
            ''', conn, params=(selected_out_room,))
            conn.close()
            
            if not booking_info.empty:
                b_data = booking_info.iloc[0]
                
                st.markdown("---")
                st.markdown("### 🧾 Hóa Đơn Thanh Toán")
                c1, c2 = st.columns(2)
                with c1:
                    st.write(f"**Số phòng:** {b_data['room_number']}")
                    st.write(f"**Tên khách hàng:** {b_data['customer_name']}")
                    st.write(f"**Số điện thoại:** {b_data['phone']}")
                with c2:
                    st.write(f"**Ngày check-in:** {b_data['check_in']}")
                    st.write(f"**Ngày check-out:** {b_data['check_out']}")
                    st.write(f"**TỔNG CỘNG:** :green[**{b_data['total_price']:,.0f} VNĐ**]")
                st.markdown("---")
                
                if st.button("🔴 Xác nhận Thanh toán & Trả phòng"):
                    checkout_room(selected_out_room)
                    st.success(f"Phòng {selected_out_room} đã thanh toán thành công và trở về trạng thái Trống!")
                    st.rerun()

# ------------------------------------------
# CHỨC NĂNG 3: QUẢN LÝ DANH MỤC PHÒNG
# ------------------------------------------
elif menu == "⚙️ Quản lý danh mục phòng":
    st.title("⚙️ Cấu Hình & Quản Lý Phòng")
    
    df_rooms = load_rooms()
    
    col_table, col_add = st.columns([2, 1])
    
    with col_table:
        st.subheader("📋 Danh sách toàn bộ phòng")
        st.dataframe(
            df_rooms.style.format({"price": "{:,.0f} VNĐ"}),
            use_container_width=True,
            height=300
        )
        
    with col_add:
        st.subheader("➕ Thêm phòng mới")
        with st.form("form_add_room"):
            new_no = st.text_input("Số phòng (VD: 104)")
            new_type = st.selectbox("Loại phòng", ["Đơn (Standard)", "Đôi (VIP)", "Gia đình (Suite)"])
            new_price = st.number_input("Giá phòng/đêm (VNĐ)", min_value=100000, value=500000, step=50000)
            
            btn_add = st.form_submit_button("Thêm phòng vào sơ đồ")
            if btn_add:
                if not new_no.strip():
                    st.error("Số phòng không được bỏ trống!")
                elif new_no in df_rooms['room_number'].values:
                    st.error("Số phòng này đã tồn tại trong hệ thống!")
                else:
                    conn = get_connection()
                    c = conn.cursor()
                    c.execute("INSERT INTO rooms VALUES (?, ?, ?, 'Trống')", (new_no, new_type, new_price))
                    conn.commit()
                    conn.close()
                    st.success(f"Đã thêm thành công phòng {new_no}!")
                    st.rerun()

    st.markdown("---")
    
    col_edit, col_del = st.columns(2)
    
    with col_edit:
        st.subheader("🛠️ Cập nhật trạng thái thủ công")
        target_room = st.selectbox("Chọn phòng cần đổi", df_rooms['room_number'].tolist(), key="select_update")
        target_status = st.selectbox("Trạng thái mới", ["Trống", "Bảo trì", "Đặt trước"])
        if st.button("Lưu thay đổi trạng thái"):
            update_room_status(target_room, target_status)
            st.success(f"Đã chuyển phòng {target_room} sang trạng thái: {target_status}")
            st.rerun()
            
    with col_del:
        st.subheader("🗑️ Xóa phòng khỏi hệ thống")
        del_room = st.selectbox("Chọn phòng cần xóa", df_rooms['room_number'].tolist(), key="select_del")
        if st.button("Xóa phòng này", type="primary"):
            room_status = df_rooms[df_rooms['room_number'] == del_room]['status'].values[0]
            if room_status == 'Đang ở':
                st.error("Không thể xóa phòng đang có khách ở!")
            else:
                delete_room(del_room)
                st.success(f"Đã xóa phòng {del_room} khỏi cơ sở dữ liệu!")
                st.rerun()

# ------------------------------------------
# CHỨC NĂNG 4: BÁO CÁO DOANH THU
# ------------------------------------------
elif menu == "📊 Báo cáo doanh thu":
    st.title("📊 Báo Cáo Doanh Thu & Thống Kê")
    
    conn = get_connection()
    df_bookings = pd.read_sql("SELECT * FROM bookings", conn)
    df_rooms = load_rooms()
    conn.close()
    
    if df_bookings.empty:
        st.info("Chưa ghi nhận bất kỳ lịch sử giao dịch nào.")
    else:
        # Chỉ số tổng quan
        revenue = df_bookings['total_price'].sum()
        total_bookings = len(df_bookings)
        completed_bookings = len(df_bookings[df_bookings['booking_status'] == 'Đã trả phòng'])
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Tổng doanh thu tích lũy", f"{revenue:,.0f} VNĐ")
        c2.metric("Tổng lượt giao dịch", total_bookings)
        c3.metric("Lượt đã hoàn thành", completed_bookings)
        
        st.markdown("---")
        
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            st.subheader("Tỷ lệ phân bổ trạng thái phòng")
            status_df = df_rooms['status'].value_counts().reset_index()
            status_df.columns = ['Trạng thái', 'Số lượng']
            fig_pie = px.pie(
                status_df, 
                names='Trạng thái', 
                values='Số lượng', 
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with col_chart2:
            st.subheader("Doanh thu theo số phòng")
            rev_by_room = df_bookings.groupby('room_number')['total_price'].sum().reset_index()
            rev_by_room.columns = ['Phòng', 'Doanh thu (VNĐ)']
            fig_bar = px.bar(
                rev_by_room, 
                x='Phòng', 
                y='Doanh thu (VNĐ)',
                text_auto='.2s',
                color_discrete_sequence=['#28a745']
            )
            st.plotly_chart(fig_bar, use_container_width=True)
            
        st.markdown("---")
        st.subheader("📋 Chi tiết lịch sử đặt phòng")
        st.dataframe(
            df_bookings.sort_values(by='id', ascending=False).style.format({"total_price": "{:,.0f} VNĐ"}),
            use_container_width=True
        )
