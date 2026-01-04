import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
import pandas as pd
import os
import jpholiday  # 日本の祝日判定用

# --- 1. 画面の設定 ---
st.set_page_config(layout="wide", page_title="週間シフト管理")

# --- 2. 認証設定 ---
def connect_to_sheet():
    if not os.path.exists("secret_key.json"):
        st.error("エラー：'secret_key.json' が見つかりません。")
        return None
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("secret_key.json", scope)
        client = gspread.authorize(creds)
        url = "https://docs.google.com/spreadsheets/d/1uOGhIG2IH-qa5lJtMp_2FaSmvPR6cnOwi1WC0yCTrUM/edit#gid=0"
        workbook = client.open_by_url(url)
        return workbook.worksheet("シート1")
    except Exception as e:
        st.sidebar.error(f"接続エラー: {e}")
        return None

# --- 3. データの初期化 ---
if 'staff_colors' not in st.session_state:
    st.session_state.staff_colors = {
        "内村": "#FFC0CB", "片岡": "#FFD700", "久保田": "#98FB98", 
        "足立": "#87CEEB", "松田": "#DDA0DD", "広我": "#F0E68C", 
        "ニコ": "#E6E6FA", "紗希": "#FFA07A", "ジョン": "#B0C4DE", 
        "米田": "#AFEEEE", "難波": "#FFDEAD", "ヘルプ": "#D3D3D3"
    }
if 'week_data' not in st.session_state: st.session_state.week_data = {}
if 'daily_memo' not in st.session_state: st.session_state.daily_memo = {}
if 'daily_biz_hours' not in st.session_state: st.session_state.daily_biz_hours = {}

staff_list = list(st.session_state.staff_colors.keys())
num_staff = len(staff_list)

# --- 4. デザイン (CSS) ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #FFFFFF; color: #333333; }}
    .block-container {{ 
        padding-top: 3rem !important; 
        max-width: 100% !important; 
    }}
    .main-title {{ font-size: 26px; font-weight: bold; margin-bottom: 25px; color: #1E1E1E; }}

    /* タブのデザイン */
    .stTabs [data-baseweb="tab-list"] {{ gap: 8px; background-color: #f0f2f6; padding: 10px 10px 0px 10px; border-radius: 8px 8px 0 0; }}
    .stTabs [data-baseweb="tab"] {{ height: 50px; background-color: #e0e0e0; border-radius: 5px 5px 0 0; padding: 0px 25px; font-size: 16px; color: #555; }}
    .stTabs [aria-selected="true"] {{ background-color: #ffffff !important; font-weight: bold; color: #000 !important; }}

    /* スマホ・PC両対応のスクロール設定 */
    .day-container {{ 
        margin-bottom: 25px; 
        border: 1px solid #000; 
        background-color: #fff; 
        overflow-x: auto; /* 横スクロールを許可 */
        -webkit-overflow-scrolling: touch;
    }}
    
    .grid-container {{
        display: grid;
        grid-template-columns: 50px 60px repeat(48, 20px) 80px 80px 80px; /* 1コマ20pxで固定 */
        width: max-content; /* 中身のサイズに合わせる */
    }}
    
    .cell-header {{ background-color: #000; color: #fff; font-weight: bold; text-align: center; font-size: 8px; height: 22px; line-height: 22px; border-right: 1px solid #555; }}
    .cell-staff {{ border-right: 1px solid #000; border-bottom: 1px solid #000; text-align: center; font-size: 10px; height: 26px; line-height: 26px; font-weight: bold; background-color: inherit; }}
    .cell-timeline {{ border-right: 1px solid #ddd; border-bottom: 1px solid #000; height: 26px; }}
    .hour-mark {{ border-right: 1px solid #000 !important; }} 
    
    .vertical-merge-cell {{
        grid-row: span {num_staff}; border-right: 1px solid #000; border-bottom: 1px solid #000;
        display: flex; align-items: center; justify-content: center; text-align: center;
        padding: 2px; font-size: 10px; font-weight: bold; background-color: #fff; word-break: break-all;
    }}
    
    /* カラー（元に戻しました） */
    .bg-rec {{ background-color: #FF0000 !important; }}
    .bg-live {{ background-color: #00B0F0 !important; }}
    .bg-others {{ background-color: #7030A0 !important; }}
    .bg-closed {{ background-color: #000000 !important; border-right: none !important; }} /* 漆黒 */
    
    /* 祝日ハイライト */
    .holiday-label {{ background-color: #FFFF00 !important; color: #FF0000 !important; }}
    </style>
""", unsafe_allow_html=True)

# --- 5. データの読み込み ---
sheet = connect_to_sheet()
df_sheet = None
if sheet:
    try:
        all_data = sheet.get_all_values()
        df_sheet = pd.DataFrame(all_data)
    except: pass

# --- 6. 営業時間の初期値計算 ---
def get_default_biz_hours(date_obj):
    is_holiday = jpholiday.is_holiday(date_obj)
    tomorrow = date_obj + timedelta(days=1)
    is_tomorrow_holiday = jpholiday.is_holiday(tomorrow)
    wd = date_obj.weekday()
    start = 9.0 if (is_holiday or wd >= 5) else 10.0
    end = 27.0 if (wd == 4 or wd == 5 or is_tomorrow_holiday) else 24.0
    return (start, end)

# --- 7. メインタイトル ---
st.markdown('<div class="main-title">📅 週間シフト管理システム</div>', unsafe_allow_html=True)

today = datetime.now()
monday_this_week = today - timedelta(days=today.weekday())
tab_titles = [f"📅 {(monday_this_week + timedelta(weeks=w)).month}/{(monday_this_week + timedelta(weeks=w)).day}週" for w in range(5)]
tabs = st.tabs(tab_titles)

weekdays_short = ["月", "火", "水", "木", "金", "土", "日"]
weekdays_full = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "日曜日"]

# --- 8. タブごとの表示 ---
for w, tab in enumerate(tabs):
    with tab:
        start_of_week = monday_this_week + timedelta(weeks=w)
        date_info = []
        for i in range(7):
            d = start_of_week + timedelta(days=i)
            p1 = f"{d.year}年{d.month}月{d.day}日{weekdays_full[d.weekday()]}"
            p2 = f"{d.year}/{d.month}/{d.day}"
            p3 = f"{d.month}/{d.day}"
            disp = f"{d.month}/{d.day}({weekdays_short[d.weekday()]})"
            is_holiday = jpholiday.is_holiday(d)
            biz_hours = st.session_state.daily_biz_hours.get(disp, get_default_biz_hours(d))
            date_info.append({
                "patterns": [p1, p2, p3], 
                "display": disp, 
                "is_holiday": is_holiday,
                "biz_start": biz_hours[0],
                "biz_end": biz_hours[1]
            })

        for info in date_info:
            rec_val, live_val = "", ""
            if df_sheet is not None:
                for idx, row in df_sheet.iterrows():
                    if any(p in str(row[0]) for p in info["patterns"]):
                        # BX列=index 74, BY列=index 75
                        rec_val = str(row[74]) if len(row) > 74 else ""
                        live_val = str(row[75]) if len(row) > 75 else ""
                        break

            st.markdown('<div class="day-container">', unsafe_allow_html=True)
            h_html = '<div class="grid-container">'
            h_html += '<div class="cell-header">日付</div><div class="cell-header">氏名</div>'
            for h in range(7, 31):
                h_disp = h if h < 24 else h - 24
                h_html += f'<div class="cell-header hour-mark" style="grid-column: span 2;">{h_disp}</div>'
            h_html += '<div class="cell-header">予定</div><div class="cell-header">REC</div><div class="cell-header">LIVE</div></div>'
            st.markdown(h_html, unsafe_allow_html=True)

            body_html = '<div class="grid-container">'
            h_class = "holiday-label" if info["is_holiday"] else ""
            body_html += f'<div class="vertical-merge-cell {h_class}">{info["display"]}</div>'
            
            for i, name in enumerate(staff_list):
                bg = st.session_state.staff_colors.get(name, "#eee")
                body_html += f'<div class="cell-staff" style="background-color:{bg}">{name}</div>'
                shift = st.session_state.week_data.get((info["display"], name))
                for j in range(48):
                    t = 7 + (j * 0.5)
                    h_line = "hour-mark" if j % 2 == 1 else ""
                    is_open = info["biz_start"] <= t < info["biz_end"]
                    c_type = ""
                    if not is_open:
                        c_type = "bg-closed"
                    elif shift and shift["start"] <= t < shift["end"]:
                        c_type = "bg-rec" if shift["type"]=="REC" else "bg-live" if shift["type"]=="ST LIVE" else "bg-others" if shift["type"]=="その他" else ""
                    body_html += f'<div class="cell-timeline {h_line} {c_type}"></div>'
                
                if i == 0:
                    memo = st.session_state.daily_memo.get(info["display"], "")
                    body_html += f'<div class="vertical-merge-cell">{memo}</div>'
                    body_html += f'<div class="vertical-merge-cell" style="color: red;">{rec_val}</div>'
                    body_html += f'<div class="vertical-merge-cell" style="color: blue;">{live_val}</div>'

            body_html += '</div></div>'
            st.markdown(body_html, unsafe_allow_html=True)

# --- 9. サイドバー ---
st.sidebar.title("🛠️ 操作パネル")
all_dates = [f"{(monday_this_week + timedelta(days=i)).month}/{(monday_this_week + timedelta(days=i)).day}({weekdays_short[(monday_this_week + timedelta(days=i)).weekday()]})" for i in range(35)]
target_date_str = st.sidebar.selectbox("対象の日付を選択", all_dates)

st.sidebar.subheader("🕘 営業時間の個別変更")
current_d_idx = all_dates.index(target_date_str)
default_biz = get_default_biz_hours(monday_this_week + timedelta(days=current_d_idx))
new_biz = st.sidebar.slider("この日の営業時間", 7.0, 31.0, st.session_state.daily_biz_hours.get(target_date_str, default_biz), step=0.5)
if st.sidebar.button("営業時間を確定"):
    st.session_state.daily_biz_hours[target_date_str] = new_biz
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("👤 シフト登録")
with st.sidebar.form("shift_input"):
    s_name = st.selectbox("スタッフ", staff_list)
    s_type = st.radio("作業", ["REC", "ST LIVE", "その他", "休み"])
    s_time = st.slider("時間帯", 7.0, 31.0, (10.0, 18.0), step=0.5)
    if st.form_submit_button("登録"):
        st.session_state.week_data[(target_date_str, s_name)] = {"type": s_type, "start": s_time[0], "end": s_time[1]}
        st.rerun()