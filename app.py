import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
import pandas as pd
import jpholiday
import json

# --- 1. ページ基本設定 ---
st.set_page_config(layout="wide", page_title="週間シフト管理")

# --- 2. 認証処理 (JWTエラー対策) ---
def connect_to_sheet():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        if "gspread_creds_json" in st.secrets:
            # 文字列をきれいに掃除してから解析
            json_text = st.secrets["gspread_creds_json"].strip()
            creds_info = json.loads(json_text)
            
            # 秘密鍵のバックスラッシュ改行を実改行に置換
            if "private_key" in creds_info:
                creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
            
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
            client = gspread.authorize(creds)
            # シートURL
            url = "https://docs.google.com/spreadsheets/d/1uOGhIG2IH-qa5lJtMp_2FaSmvPR6cnOwi1WC0yCTrUM/edit#gid=0"
            return client.open_by_url(url).worksheet("シート1")
    except Exception as e:
        st.sidebar.error(f"接続エラー: {e}")
        return None

# --- 3. セッション管理 ---
if 'week_data' not in st.session_state: st.session_state.week_data = {}
staff_colors = {
    "内村": "#FFC0CB", "片岡": "#FFD700", "久保田": "#98FB98", "足立": "#87CEEB",
    "松田": "#DDA0DD", "広我": "#F0E68C", "ニコ": "#E6E6FA", "紗希": "#FFA07A",
    "ジョン": "#B0C4DE", "米田": "#AFEEEE", "難波": "#FFDEAD", "ヘルプ": "#D3D3D3"
}
staff_list = list(staff_colors.keys())

# --- 4. CSS (デザインの要) ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #f8f9fa; }}
    .main-title {{ font-size: 28px; font-weight: bold; color: #333; margin-bottom: 20px; }}
    .day-container {{ background: white; border: 2px solid #333; margin-bottom: 30px; box-shadow: 4px 4px 0px #888; }}
    .grid-container {{ display: grid; grid-template-columns: 60px 80px repeat(48, 15px) 100px 80px 80px; width: max-content; }}
    .cell {{ border-right: 1px solid #ddd; border-bottom: 1px solid #333; height: 30px; line-height: 30px; text-align: center; font-size: 11px; }}
    .header {{ background-color: #333; color: white; font-size: 9px; font-weight: bold; border-right: 1px solid #555; }}
    .staff-name {{ font-weight: bold; border-right: 2px solid #333; }}
    .hour-border {{ border-right: 2px solid #333 !important; }}
    .merge-col {{ grid-row: span {len(staff_list)}; display: flex; align-items: center; justify-content: center; font-weight: bold; border-right: 2px solid #333; }}
    .holiday-bg {{ background-color: #fff9c4 !important; color: #d32f2f; }}
    .bg-rec {{ background-color: #ff5252 !important; }}
    .bg-live {{ background-color: #40c4ff !important; }}
    .bg-other {{ background-color: #b388ff !important; }}
    .bg-closed {{ background-color: #444 !important; }}
    </style>
""", unsafe_allow_html=True)

# --- 5. メインロジック ---
sheet = connect_to_sheet()
df_sheet = None
if sheet:
    try: df_sheet = pd.DataFrame(sheet.get_all_values())
    except: pass

st.markdown('<div class="main-title">📅 シフト管理システム</div>', unsafe_allow_html=True)

today = datetime.now()
monday = today - timedelta(days=today.weekday())
tabs = st.tabs([f"{(monday + timedelta(weeks=w)).month}/{(monday + timedelta(weeks=w)).day}週" for w in range(5)])

for w, tab in enumerate(tabs):
    with tab:
        for i in range(7):
            d = monday + timedelta(weeks=w, days=i)
            is_hol = jpholiday.is_holiday(d)
            disp = f"{d.month}/{d.day}\n({['月','火','水','木','金','土','日'][d.weekday()]})"
            
            st.markdown('<div class="day-container">', unsafe_allow_html=True)
            
            # ヘッダー (時間軸)
            h_html = '<div class="grid-container"><div class="cell header">日付</div><div class="cell header staff-name">氏名</div>'
            for h in range(7, 31): h_html += f'<div class="cell header hour-border" style="grid-column: span 2;">{h if h < 24 else h-24}</div>'
            st.markdown(h_html + '<div class="cell header">予定</div><div class="cell header">REC</div><div class="cell header">LIVE</div></div>', unsafe_allow_html=True)
            
            # スタッフデータ表示
            body = f'<div class="grid-container"><div class="cell merge-col {"holiday-bg" if is_hol else ""}">{disp}</div>'
            for idx, name in enumerate(staff_list):
                if idx > 0: body += f'<div class="cell" style="grid-column: 2;"></div>' # ダミー
                body += f'<div class="cell staff-name" style="background-color:{staff_colors[name]}">{name}</div>'
                
                # シフト（現在はサンプルとして空表示）
                for j in range(48):
                    border = "hour-border" if j % 2 == 1 else ""
                    body += f'<div class="cell {border}"></div>'
                
                if idx == 0:
                    body += f'<div class="cell merge-col">予定メモ</div><div class="cell merge-col">REC値</div><div class="cell merge-col">LIVE値</div>'
            st.markdown(body + '</div></div>', unsafe_allow_html=True)

# --- 6. サイドバー ---
st.sidebar.title("🛠 設定")
if sheet: st.sidebar.success("Googleシート接続中")
else: st.sidebar.error("シート未接続")
