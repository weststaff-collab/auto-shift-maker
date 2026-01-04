import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
import pandas as pd
import jpholiday

# --- 1. ページ基本設定 ---
st.set_page_config(layout="wide", page_title="週間シフト管理")

# --- 2. 認証処理 (成功している設定を維持) ---
def get_gspread_client():
    try:
        creds_dict = {
            "type": "service_account",
            "project_id": "dauntless-motif-294307",
            "private_key_id": "51309e4d6320e1bb0748ce1f5a6c886e44c5cabc",
            "private_key": st.secrets["PRIVATE_KEY"], 
            "client_email": "west-shift-app@dauntless-motif-294307.iam.gserviceaccount.com",
            "client_id": "114530383906045619062",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/west-shift-app%40dauntless-motif-294307.iam.gserviceaccount.com"
        }
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        return gspread.authorize(creds)
    except:
        return None

# --- 3. CSS (レイアウトを壊さないための最小限の記述) ---
st.markdown("""
<style>
    .scroll-box { overflow-x: auto; width: 100%; border: 1px solid #000; background: #fff; }
    table { border-collapse: collapse; width: 100%; min-width: 1200px; }
    th, td { border: 1px solid #333; text-align: center; font-size: 11px; padding: 2px; }
    .th-black { background: #333; color: white; }
    .staff-name { font-weight: bold; width: 80px; }
    .hour-cell { width: 15px; }
    .rec-live { width: 80px; font-weight: bold; font-size: 14px; }
</style>
""", unsafe_allow_html=True)

# --- 4. データ取得 ---
client = get_gspread_client()
df = None
if client:
    try:
        sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1uOGhIG2IH-qa5lJtMp_2FaSmvPR6cnOwi1WC0yCTrUM/edit#gid=0").worksheet("シート1")
        df = pd.DataFrame(sheet.get_all_values())
    except:
        st.error("データの読み込みに失敗しました")

# --- 5. 表示 ---
st.title("📅 週間シフト管理")
staff_list = ["内村", "片岡", "久保田", "足立", "松田", "広我", "ニコ", "紗希", "ジョン", "米田", "難波", "ヘルプ"]
staff_colors = {"内村":"#FFC0CB", "片岡":"#FFD700", "久保田":"#98FB98", "足立":"#87CEEB", "松田":"#DDA0DD", "広我":"#F0E68C", "ニコ":"#E6E6FA", "紗希":"#FFA07A", "ジョン":"#B0C4DE", "米田":"#AFEEEE", "難波":"#FFDEAD", "ヘルプ":"#D3D3D3"}

today = datetime.now()
monday = today - timedelta(days=today.weekday())

for i in range(7):
    d = monday + timedelta(days=i)
    d_str = f"{d.month}/{d.day}"
    is_hol = jpholiday.is_holiday(d)
    
    # データ抽出
    rec_val, live_val = "", ""
    if df is not None:
        row_data = df[df[0].astype(str).str.contains(d_str)]
        if not row_data.empty:
            rec_val = row_data.iloc[0, 74] if len(row_data.columns) > 74 else ""
            live_val = row_data.iloc[0, 75] if len(row_data.columns) > 75 else ""

    st.subheader(f"{d_str} ({['月','火','水','木','金','土','日'][d.weekday()]})")
    
    html = '<div class="scroll-box"><table>'
    # ヘッダー
    html += '<tr><th class="th-black">名前</th>'
    for h in range(7, 31):
        html += f'<th class="th-black" colspan="2">{h if h<24 else h-24}</th>'
    html += '<th class="th-black">REC</th><th class="th-black">LIVE</th></tr>'
    
    # スタッフ行
    for idx, name in enumerate(staff_list):
        bg = staff_colors.get(name, "#fff")
        html += f'<tr><td class="staff-name" style="background:{bg};">{name}</td>'
        for _ in range(48): html += '<td class="hour-cell"></td>'
        
        if idx == 0:
            html += f'<td rowspan="{len(staff_list)}" class="rec-live" style="color:red;">{rec_val}</td>'
            html += f'<td rowspan="{len(staff_list)}" class="rec-live" style="color:blue;">{live_val}</td>'
        html += '</tr>'
        
    html += '</table></div><br>'
    st.markdown(html, unsafe_allow_html=True)
