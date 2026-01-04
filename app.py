import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
import pandas as pd
import jpholiday
import json

# --- 1. 画面の設定 ---
st.set_page_config(layout="wide", page_title="週間シフト管理")

# --- 2. 認証設定 (TOML & Escape問題を完全解決) ---
def connect_to_sheet():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        
        if "gspread_creds_json" in st.secrets:
            # SecretsからJSON文字列をそのまま取得
            json_str = st.secrets["gspread_creds_json"]
            creds_info = json.loads(json_str)
            
            # 秘密鍵の改行処理 (バックスラッシュnを実際の改行に)
            if "private_key" in creds_info:
                creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
            
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
        else:
            st.error("Secretsに 'gspread_creds_json' が設定されていません。")
            return None
        
        client = gspread.authorize(creds)
        url = "https://docs.google.com/spreadsheets/d/1uOGhIG2IH-qa5lJtMp_2FaSmvPR6cnOwi1WC0yCTrUM/edit#gid=0"
        workbook = client.open_by_url(url)
        return workbook.worksheet("シート1")
    except Exception as e:
        st.sidebar.error(f"接続エラー: {e}")
        return None

# --- 3. セッション管理とスタッフリスト ---
if 'staff_colors' not in st.session_state:
    st.session_state.staff_colors = {
        "内村": "#FFC0CB", "片岡": "#FFD700", "久保田": "#98FB98", 
        "足立": "#87CEEB", "松田": "#DDA0DD", "広我": "#F0E68C", 
        "ニコ": "#E6E6FA", "紗希": "#FFA07A", "ジョン": "#B0C4DE", 
        "米田": "#AFEEEE", "難波": "#FFDEAD", "ヘルプ": "#D3D3D3"
    }
staff_list = list(st.session_state.staff_colors.keys())

# --- 4. デザイン ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; }
    .main-title { font-size: 24px; font-weight: bold; margin-bottom: 20px; }
    .day-container { margin-bottom: 25px; border: 1px solid #000; overflow-x: auto; }
    .grid-container { display: grid; grid-template-columns: 50px 60px repeat(48, 20px) 80px 80px 80px; width: max-content; }
    .cell-header { background-color: #000; color: #fff; font-size: 8px; text-align: center; border-right: 1px solid #555; }
    .cell-staff { border-right: 1px solid #000; border-bottom: 1px solid #000; text-align: center; font-size: 10px; font-weight: bold; height: 26px; }
    .cell-timeline { border-right: 1px solid #ddd; border-bottom: 1px solid #000; height: 26px; }
    .vertical-merge { grid-row: span 12; border-right: 1px solid #000; border-bottom: 1px solid #000; display: flex; align-items: center; justify-content: center; font-size: 10px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- 5. メイン表示 ---
sheet = connect_to_sheet()
df_sheet = None
if sheet:
    try:
        df_sheet = pd.DataFrame(sheet.get_all_values())
    except: pass

st.markdown('<div class="main-title">📅 週間シフト管理システム</div>', unsafe_allow_html=True)

today = datetime.now()
monday = today - timedelta(days=today.weekday())
tabs = st.tabs([f"{(monday + timedelta(weeks=w)).month}/{(monday + timedelta(weeks=w)).day}週" for w in range(5)])

for w, tab in enumerate(tabs):
    with tab:
        for i in range(7):
            d = monday + timedelta(weeks=w, days=i)
            disp = f"{d.month}/{d.day}"
            
            st.markdown(f'<div class="day-container">', unsafe_allow_html=True)
            # 簡易ヘッダー表示
            h_html = f'<div class="grid-container"><div class="cell-header">日付</div><div class="cell-header">名前</div>'
            for hr in range(7, 31): h_html += f'<div class="cell-header" style="grid-column: span 2;">{hr if hr < 24 else hr-24}</div>'
            st.markdown(h_html + '</div>', unsafe_allow_html=True)
            
            # スタッフ行
            body_html = f'<div class="grid-container"><div class="vertical-merge">{disp}</div>'
            for idx, name in enumerate(staff_list):
                if idx > 0: body_html += f'<div class="grid-container">'
                body_html += f'<div class="cell-staff" style="background-color:{st.session_state.staff_colors[name]}">{name}</div>'
                for _ in range(48): body_html += '<div class="cell-timeline"></div>'
                if idx == 0: body_html += '<div class="vertical-merge">予定</div><div class="vertical-merge">REC</div><div class="vertical-merge">LIVE</div>'
            st.markdown(body_html + '</div></div>', unsafe_allow_html=True)

st.sidebar.success("接続設定を完了しました。")
