import sqlite3
import pandas as pd
import plotly.express as px
import streamlit as st
from datetime import datetime, date

# ==========================================
# 1. CẤU HÌNH TRANG VÀ CSS TÙY CHỈNH
# ==========================================
st.set_page_config(
    page_title="Hệ Thống Quản Lý Khách Sạn - HMS Pro 100 Phòng",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .main { padding: 1.2rem; }
    .stMetric {
        background-color: #ffffff;
        padding: 12px;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 2px 5px rgba(0,0,0,0.03);
    }
    .room-card {
        padding: 12px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 12px;
        box-shadow: 0 3px 6px rgba(0,0,0,0.1);
    }
    .room-card h3 { margin: 0 0 5px 0; color: white; font-size: 20px; }
    .room-card p { margin: 2px 0; font-size: 13px; }
    .status-trong { background: linear-gradient(135deg, #28a745, #20c997); }
    .status-dang-o { background: linear-gradient(135deg, #dc3545, #ff6b6b); }
    .status-dat-truoc { background: linear-gradient(135deg, #ffc107, #ffda6a); color: #856404 !important; }
    .status-dat-truoc h3 { color: #856404 !important; }
    .status-bao-tri { background: linear-gradient(135deg, #6c757d, #adb5bd); }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. XỬ LÝ CƠ SỞ DỮ LIỆU
# ==========================================
DB_FILE = "hotel_management.db"

def get_connection():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    
    # Bảng phòng
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
            service_fee REAL DEFAULT 0,
            booking_status TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Bảng dịch vụ (Minibar, giặt ủi...)
    c.execute('''
        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_id INTEGER NOT NULL,
            service_name TEXT NOT NULL,
            amount REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (booking_id) REFERENCES bookings (id)
        )
    ''')
    
    conn.commit()
    conn.close()

init_db()

# Hàm ép tạo mới/reset đủ 100 phòng
def seed_100_rooms():
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM rooms")
    
    rooms_data = []
    # Tạo 5 tầng, mỗi tầng 20 phòng (Tổng = 100 phòng)
    for floor in range(1, 6):
        for r in range(1, 21):
            room_num = f"{floor}{r:02d}"  # VD: 101, 102... 520
            
            if floor in [1, 2]:
                room_type = "Đơn (Standard)"
                price = 500000
            elif floor in [3, 4]:
                room_type = "Đôi (VIP)"
                price = 800000
            else:
                room_type = "Gia đình (Suite)"
                price = 1500000
            
            status = "Trống"
            if r in [2, 5]:
                status = "Đang ở"
            elif r == 8:
                status = "Đặt trước"
            elif r == 12:
                status = "Bảo trì"
                
            rooms_data.append((room_num, room_type, price, status))
            
    c.executemany("INSERT INTO rooms VALUES (?, ?, ?, ?)", rooms_data)
    
    # Tạo booking mẫu cho các phòng đang ở
    c.execute("DELETE FROM bookings")
    c.execute('''
        INSERT INTO bookings (room_number, customer_name, phone, check_in, check_out, total_price, service_fee, booking_status)
        VALUES ('102', 'Nguyễn Văn A', '0901234567', ?, ?, 500000, 50000, 'Đã nhận phòng')
    ''', (date.today().strftime('%Y-%m-%d'), date.today().strftime('%Y-%m-%d')))
    
    conn.commit()
    conn.close()

# ==========================================
# 3. HÀM TRUY VẤN
# ==========================================
def load_rooms():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM rooms ORDER BY CAST(room_number AS INTEGER) ASC", conn)
    conn.close()
    return df

def update_room_status(room_number, new_status):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE rooms SET status = ? WHERE room_number = ?", (new_status, room_number))
    conn.commit()
    conn.close()

def create_booking(room_number, customer_name, phone, check_in, check_out, total_price, is_reservation=False):
    conn = get_connection()
    c = conn.cursor()
    status_str = 'Đặt trước' if is_reservation else 'Đã nhận phòng'
    room_status = 'Đặt trước' if is_reservation else 'Đang ở'
    
    c.execute('''
        INSERT INTO bookings (room_number, customer_name, phone, check_in, check_out, total_price, service_fee, booking_status)
        VALUES (?, ?, ?, ?, ?, ?, 0, ?)
    ''', (room_number, customer_name, phone, check_in, check_out, total_price, status_str))
    
    c.execute("UPDATE rooms SET status = ? WHERE room_number = ?", (room_status, room_number))
    conn.commit()
    conn.close()

def add_service(booking_id, service_name, amount):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO services (booking_id, service_name, amount) VALUES (?, ?, ?)", (booking_id, service_name, amount))
    c.execute("UPDATE bookings SET service_fee = service_fee + ? WHERE id = ?", (amount, booking_id))
    conn.commit()
    conn.close()

def checkout_room(room_number):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE rooms SET status = 'Trống' WHERE room_number = ?", (room_number,))
    c.execute("UPDATE bookings SET booking_status = 'Đã trả phòng' WHERE room_number = ? AND booking_status = 'Đã nhận phòng'", (room_number,))
    conn.commit()
    conn.close()

# ==========================================
# 4. SIDEBAR - THANH ĐIỀU HƯỚNG
# ==========================================
st.sidebar.title("🏨 HMS PRO - 100 PHÒNG")
st.sidebar.markdown("---")

menu = st.sidebar.radio(
    "CHỨC NĂNG CHÍNH",
    [
        "📌 Sơ đồ phòng Live", 
        "🔑 Nhận & Trả phòng", 
        "🍹 Gọi Dịch vụ / Minibar",
        "⚙️ Quản lý danh mục phòng", 
        "📊 Báo cáo doanh thu"
    ]
)

st.sidebar.markdown("---")

# NÚT KHÔI PHỤC ĐỦ 100 PHÒNG
if st.sidebar.button("🔄 Khởi tạo lại đủ 100 phòng"):
    seed_100_rooms()
    st.sidebar.success("Đã khởi tạo lại danh sách 100 phòng thành công!")
    st.rerun()

# ------------------------------------------
# CHỨC NĂNG 1: SƠ ĐỒ PHÒNG LIVE
# ------------------------------------------
if menu == "📌 Sơ đồ phòng Live":
    st.title("📌 Sơ Đồ Phòng Theo Thời Gian Thực")
    
    df_rooms = load_rooms()
    
    # Metrics
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
    
    # Lọc Tầng & Trạng thái
    col_f1, col_f2 = st.columns([1, 2])
    with col_f1:
        df_rooms['Floor'] = df_rooms['room_number'].apply(lambda x: f"Tầng {x[0]}")
        selected_floors = st.multiselect(
            "Lọc theo Tầng:",
            options=sorted(df_rooms['Floor'].unique()),
            default=sorted(df_rooms['Floor'].unique())
        )
    with col_f2:
        filter_status = st.multiselect(
            "Lọc theo Trạng thái:",
            options=["Trống", "Đang ở", "Đặt trước", "Bảo trì"],
            default=["Trống", "Đang ở", "Đặt trước", "Bảo trì"]
        )
    
    filtered_rooms = df_rooms[(df_rooms['status'].isin(filter_status)) & (df_rooms['Floor'].isin(selected_floors))]
    
    if filtered_rooms.empty:
        st.warning("Không tìm thấy phòng phù hợp với bộ lọc!")
    else:
        cols = st.columns(5)
        status_class = {
            "Trống": "status-trong",
            "Đang ở": "status-dang-o",
            "Đặt trước": "status-dat-truoc",
            "Bảo trì": "status-bao-tri"
        }
        
        for idx, row in filtered_rooms.reset_index(drop=True).iterrows():
            col_idx = idx % 5
            css_cls = status_class.get(row['status'], "")
            with cols[col_idx]:
                st.markdown(
                    f"""
                    <div class="room-card {css_cls}">
                        <h3>P. {row['room_number']}</h3>
                        <p><b>{row['room_type']}</b></p>
                        <p><b>{row['status']}</b></p>
                        <p>{row['price']:,.0f} đ/đêm</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

# ------------------------------------------
# CHỨC NĂNG 2: NHẬN PHÒNG & TRẢ PHÒNG
# ------------------------------------------
elif menu == "🔑 Nhận & Trả phòng":
    st.title("🔑 Lễ Tân - Nhận / Đặt & Trả Phòng")
    
    tab1, tab2, tab3 = st.tabs(["📝 Check-in (Nhận ngay)", "📅 Đặt phòng trước", "💳 Check-out (Trả phòng)"])
    df_rooms = load_rooms()
    
    # TAB 1: CHECK-IN
    with tab1:
        st.subheader("Đăng ký nhận phòng ngay")
        available_rooms = df_rooms[df_rooms['status'] == 'Trống']
        
        if available_rooms.empty:
            st.error("Hiện không có phòng trống nào!")
        else:
            with st.form("form_checkin"):
                col_a, col_b = st.columns(2)
                with col_a:
                    selected_room = st.selectbox("Chọn phòng trống", available_rooms['room_number'].tolist())
                    customer_name = st.text_input("Họ và tên khách hàng (*)")
                    phone = st.text_input("Số điện thoại / CCCD (*)")
                with col_b:
                    check_in_date = st.date_input("Ngày nhận phòng", date.today())
                    check_out_date = st.date_input("Ngày trả phòng dự kiến", date.today())
                    
                    room_info = available_rooms[available_rooms['room_number'] == selected_room].iloc[0]
                    days = max((check_out_date - check_in_date).days, 1)
                    est_price = days * room_info['price']
                    
                    st.info(f"Loại phòng: **{room_info['room_type']}** | Tiền phòng dự tính ({days} đêm): **{est_price:,.0f} VNĐ**")
                
                if st.form_submit_button("Xác nhận Check-in"):
                    if not customer_name.strip() or not phone.strip():
                        st.error("Vui lòng nhập đầy đủ Tên và Số điện thoại!")
                    else:
                        create_booking(selected_room, customer_name, phone, check_in_date, check_out_date, est_price)
                        st.success(f"Đã nhận phòng thành công cho Phòng {selected_room}!")
                        st.rerun()

    # TAB 2: ĐẶT TRƯỚC
    with tab2:
        st.subheader("Tạo lịch đặt phòng trước (Reservation)")
        available_rooms = df_rooms[df_rooms['status'] == 'Trống']
        
        if available_rooms.empty:
            st.error("Không có phòng trống để đặt trước!")
        else:
            with st.form("form_reserve"):
                col_a, col_b = st.columns(2)
                with col_a:
                    res_room = st.selectbox("Chọn phòng", available_rooms['room_number'].tolist(), key="res_room")
                    res_name = st.text_input("Họ và tên khách đặt (*)", key="res_name")
                    res_phone = st.text_input("Số điện thoại (*)", key="res_phone")
                with col_b:
                    res_in = st.date_input("Ngày nhận dự kiến", date.today(), key="res_in")
                    res_out = st.date_input("Ngày trả dự kiến", date.today(), key="res_out")
                    
                    room_info = available_rooms[available_rooms['room_number'] == res_room].iloc[0]
                    days = max((res_out - res_in).days, 1)
                    est_price = days * room_info['price']
                    st.warning(f"Đặt trước phòng: **{res_room}** | Tiền phòng: **{est_price:,.0f} VNĐ**")
                    
                if st.form_submit_button("Lưu lịch đặt trước"):
                    if not res_name.strip() or not res_phone.strip():
                        st.error("Vui lòng nhập Tên và Số điện thoại khách đặt!")
                    else:
                        create_booking(res_room, res_name, res_phone, res_in, res_out, est_price, is_reservation=True)
                        st.success(f"Đã giữ phòng {res_room} cho khách {res_name}!")
                        st.rerun()

    # TAB 3: CHECK-OUT
    with tab3:
        st.subheader("Thanh toán & Trả phòng")
        occupied_rooms = df_rooms[df_rooms['status'] == 'Đang ở']
        
        if occupied_rooms.empty:
            st.info("Không có phòng nào đang có khách ở.")
        else:
            selected_out_room = st.selectbox("Chọn phòng trả", occupied_rooms['room_number'].tolist())
            
            conn = get_connection()
            booking_info = pd.read_sql('''
                SELECT * FROM bookings 
                WHERE room_number = ? AND booking_status = 'Đã nhận phòng'
                ORDER BY id DESC LIMIT 1
            ''', conn, params=(selected_out_room,))
            
            if not booking_info.empty:
                b_data = booking_info.iloc[0]
                b_id = b_data['id']
                
                # Chi tiết dịch vụ đã dùng
                services_df = pd.read_sql("SELECT service_name, amount, created_at FROM services WHERE booking_id = ?", conn, params=(b_id,))
                conn.close()
                
                room_fee = b_data['total_price']
                service_fee = b_data['service_fee']
                final_total = room_fee + service_fee
                
                st.markdown("---")
                st.markdown("### 🧾 Hóa Đơn Thanh Toán")
                c1, c2 = st.columns(2)
                with c1:
                    st.write(f"**Số phòng:** {b_data['room_number']}")
                    st.write(f"**Khách hàng:** {b_data['customer_name']} ({b_data['phone']})")
                    st.write(f"**Thời gian ở:** {b_data['check_in']} ➜ {b_data['check_out']}")
                with c2:
                    st.write(f"**Tiền phòng:** {room_fee:,.0f} VNĐ")
                    st.write(f"**Tiền dịch vụ / Minibar:** {service_fee:,.0f} VNĐ")
                    st.markdown(f"### **TỔNG CỘNG: :green[{final_total:,.0f} VNĐ]**")
                
                if not services_df.empty:
                    st.write("**Chi tiết dịch vụ đã dùng:**")
                    st.dataframe(services_df, use_container_width=True)
                
                st.markdown("---")
                if st.button("🔴 Xác nhận Thanh toán & Trả phòng", type="primary"):
                    checkout_room(selected_out_room)
                    st.success(f"Phòng {selected_out_room} đã thanh toán thành công!")
                    st.rerun()

# ------------------------------------------
# CHỨC NĂNG 3: GỌI DỊCH VỤ / MINIBAR
# ------------------------------------------
elif menu == "🍹 Gọi Dịch vụ / Minibar":
    st.title("🍹 Quản Lý Dịch Vụ Phòng (Minibar & Giặt ủi)")
    
    df_rooms = load_rooms()
    occupied_rooms = df_rooms[df_rooms['status'] == 'Đang ở']
    
    if occupied_rooms.empty:
        st.warning("Hiện không có phòng nào đang có khách ở để dùng dịch vụ.")
    else:
        col_s1, col_s2 = st.columns(2)
        
        with col_s1:
            target_room = st.selectbox("Chọn phòng sử dụng dịch vụ", occupied_rooms['room_number'].tolist())
            
            conn = get_connection()
            b_info = pd.read_sql("SELECT id, customer_name FROM bookings WHERE room_number = ? AND booking_status = 'Đã nhận phòng' ORDER BY id DESC LIMIT 1", conn, params=(target_room,))
            conn.close()
            
            if not b_info.empty:
                booking_id = b_info.iloc[0]['id']
                cust_name = b_info.iloc[0]['customer_name']
                st.info(f"Đang gọi dịch vụ cho khách: **{cust_name}** (Phòng {target_room})")
                
                # Danh mục dịch vụ có sẵn
                service_catalog = {
                    "Nước suối Minibar": 15000,
                    "Coca / Pepsi Minibar": 20000,
                    "Bia Heineken / Tiger": 35000,
                    "Mì ly / Snack": 25000,
                    "Giặt ủi quần áo": 50000,
                    "Ăn sáng tại phòng": 100000,
                    "Dịch vụ khác (Nhập tay)": 0
                }
                
                selected_service = st.selectbox("Chọn loại dịch vụ / món đồ", list(service_catalog.keys()))
                
                if selected_service == "Dịch vụ khác (Nhập tay)":
                    custom_service_name = st.text_input("Tên dịch vụ")
                    custom_price = st.number_input("Giá dịch vụ (VNĐ)", min_value=10000, step=10000, value=50000)
                    srv_name = custom_service_name
                    srv_price = custom_price
                else:
                    srv_name = selected_service
                    srv_price = service_catalog[selected_service]
                    st.write(f"Đơn giá: **{srv_price:,.0f} VNĐ**")
                    
                quantity = st.number_input("Số lượng", min_value=1, value=1, step=1)
                total_srv_price = srv_price * quantity
                
                if st.button("➕ Thêm vào hóa đơn phòng"):
                    if not srv_name:
                        st.error("Vui lòng nhập tên dịch vụ!")
                    else:
                        add_service(booking_id, f"{srv_name} (x{quantity})", total_srv_price)
                        st.success(f"Đã thêm **{srv_name}** ({total_srv_price:,.0f} VNĐ) vào phòng {target_room}!")
                        st.rerun()

        with col_s2:
            st.subheader("📋 Dịch vụ phòng này đã dùng")
            if 'booking_id' in locals():
                conn = get_connection()
                df_used = pd.read_sql("SELECT service_name AS 'Dịch vụ', amount AS 'Thành tiền (VNĐ)', created_at AS 'Thời gian' FROM services WHERE booking_id = ?", conn, params=(booking_id,))
                conn.close()
                
                if df_used.empty:
                    st.write("Chưa dùng dịch vụ nào.")
                else:
                    st.dataframe(df_used.style.format({"Thành tiền (VNĐ)": "{:,.0f}"}), use_container_width=True)

# ------------------------------------------
# CHỨC NĂNG 4: QUẢN LÝ DANH MỤC PHÒNG
# ------------------------------------------
elif menu == "⚙️ Quản lý danh mục phòng":
    st.title("⚙️ Cấu Hình & Quản Lý 100 Phòng")
    
    df_rooms = load_rooms()
    
    col_table, col_add = st.columns([2, 1])
    
    with col_table:
        st.subheader("📋 Danh sách toàn bộ phòng trong hệ thống")
        st.dataframe(
            df_rooms.style.format({"price": "{:,.0f} VNĐ"}),
            use_container_width=True,
            height=400
        )
        
    with col_add:
        st.subheader("➕ Thêm phòng mới thủ công")
        with st.form("form_add_room"):
            new_no = st.text_input("Số phòng (VD: 601)")
            new_type = st.selectbox("Loại phòng", ["Đơn (Standard)", "Đôi (VIP)", "Gia đình (Suite)"])
            new_price = st.number_input("Giá phòng/đêm (VNĐ)", min_value=100000, value=500000, step=50000)
            
            if st.form_submit_button("Thêm phòng"):
                if not new_no.strip():
                    st.error("Chưa nhập số phòng!")
                elif new_no in df_rooms['room_number'].values:
                    st.error("Số phòng đã tồn tại!")
                else:
                    conn = get_connection()
                    c = conn.cursor()
                    c.execute("INSERT INTO rooms VALUES (?, ?, ?, 'Trống')", (new_no, new_type, new_price))
                    conn.commit()
                    conn.close()
                    st.success(f"Đã thêm phòng {new_no}!")
                    st.rerun()

    st.markdown("---")
    c_status, c_del = st.columns(2)
    with c_status:
        st.subheader("🛠️ Đổi trạng thái phòng (Bảo trì / Trống)")
        t_room = st.selectbox("Chọn phòng", df_rooms['room_number'].tolist())
        t_status = st.selectbox("Trạng thái mới", ["Trống", "Bảo trì", "Đặt trước"])
        if st.button("Cập nhật trạng thái"):
            update_room_status(t_room, t_status)
            st.success(f"Đã chuyển phòng {t_room} sang '{t_status}'!")
            st.rerun()

# ------------------------------------------
# CHỨC NĂNG 5: BÁO CÁO DOANH THU
# ------------------------------------------
elif menu == "📊 Báo cáo doanh thu":
    st.title("📊 Báo Cáo Doanh Thu & Thống Kê")
    
    conn = get_connection()
    df_bookings = pd.read_sql("SELECT * FROM bookings", conn)
    df_rooms = load_rooms()
    conn.close()
    
    if df_bookings.empty:
        st.info("Chưa có dữ liệu giao dịch.")
    else:
        df_bookings['grand_total'] = df_bookings['total_price'] + df_bookings['service_fee']
        
        rev_total = df_bookings['grand_total'].sum()
        rev_room = df_bookings['total_price'].sum()
        rev_service = df_bookings['service_fee'].sum()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Tổng doanh thu toàn bộ", f"{rev_total:,.0f} VNĐ")
        c2.metric("Doanh thu tiền phòng", f"{rev_room:,.0f} VNĐ")
        c3.metric("Doanh thu Minibar/Dịch vụ", f"{rev_service:,.0f} VNĐ")
        
        st.markdown("---")
        
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.subheader("Tỷ lệ phân bổ trạng thái 100 phòng")
            st_counts = df_rooms['status'].value_counts().reset_index()
            st_counts.columns = ['Trạng thái', 'Số lượng']
            fig_p = px.pie(st_counts, names='Trạng thái', values='Số lượng', hole=0.4)
            st.plotly_chart(fig_p, use_container_width=True)
            
        with col_c2:
            st.subheader("Top phòng đem lại doanh thu cao nhất")
            rev_room_df = df_bookings.groupby('room_number')['grand_total'].sum().reset_index().sort_values(by='grand_total', ascending=False).head(10)
            fig_b = px.bar(rev_room_df, x='room_number', y='grand_total', text_auto='.2s', labels={'room_number': 'Phòng', 'grand_total': 'Doanh thu (VNĐ)'})
            st.plotly_chart(fig_b, use_container_width=True)
            
        st.markdown("---")
        st.subheader("📋 Chi tiết lịch sử giao dịch")
        
        st.dataframe(
            df_bookings.sort_values(by='id', ascending=False).style.format({
                "total_price": "{:,.0f}",
                "service_fee": "{:,.0f}",
                "grand_total": "{:,.0f}"
            }),
            use_container_width=True
        )
        
        # Nút xuất file CSV báo cáo
        csv_data = df_bookings.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 Tải Báo Cáo Giao Dịch (File CSV/Excel)",
            data=csv_data,
            file_name=f"Bao_Cao_Doanh_Thu_{date.today()}.csv",
            mime="text/csv"
        )
