import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
import pandas as pd
import jpholiday

# --- 1. ページ基本設定 ---
st.set_page_config(layout="wide", page_title="週間シフト管理")

# --- 2. 認証処理 (現在の成功している設定を維持) ---
def get_gspread_client():
    try:
        creds_dict = {
            "type": "service_account",
            "project_id": "dauntless-motif-294307",
            "private_key_id": "51309e4d6320e1bb0748ce1f5a6c886e44c5cabc",
            "private_key": st.secrets["PRIVATE_KEY"], # 成功したSecretsを参照
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
    except Exception as e:
        return None

# --- 3. デザイン (レイアウト崩れ防止) ---
st.markdown("""
<style>
    .reportview-container .main .block-container { max-width: 100%; padding: 10px; }
    .shift-table-wrapper { overflow-x: auto; white-space: nowrap; border: 1px solid #333; }
    .grid-container { 
        display: grid; 
        grid-template-columns: 60px 80px repeat(48, 18px) 100px 80px 80px; 
        width: 1350px; 
        background-color: #333;
        gap: 0.5px;
        border: 1px solid #333;
    }
    .cell { background: white; height: 30px; line-height: 30px; text-align: center; font-size: 11px; color: #333; }
    .header { background: #333 !important; color: white !important; font-weight: bold; font-size: 10px; }
    .staff-cell { font-weight: bold; border-right: 1px solid #333; }
    .hour-marker { border-right: 1px solid #333 !important; }
    .holiday-bg { background-color: #fff9c4 !important; color: #d32f2f; }
</style>
""", unsafe_allow_html=True)

# --- 4. データ読み込み ---
client = get_gspread_client()
df_sheet = None
if client:
    try:
        # スプレッドシートを開く
        sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1uOGhIG2IH-qa5lJtMp_2FaSmvPR6cnOwi1WC0yCTrUM/edit#gid=0").worksheet("シート1")
        all_vals = sheet.get_all_values()
        df_sheet = pd.DataFrame(all_vals)
        st.sidebar.success("データ同期中")
    except Exception as e:
        st.sidebar.error(f"シート読み込み失敗: {e}")

# --- 5. 表示ロジック ---
st.title("📅 週間シフト管理")

staff_list = ["内村", "片岡", "久保田", "足立", "松田", "広我", "ニコ", "紗希", "ジョン", "米田", "難波", "ヘルプ"]
staff_colors = {"内村":"#FFC0CB", "片岡":"#FFD700", "久保田":"#98FB98", "足立":"#87CEEB", "松田":"#DDA0DD", "広我":"#F0E68C", "ニコ":"#E6E6FA", "紗希":"#FFA07A", "ジョン":"#B0C4DE", "米田":"#AFEEEE", "難波":"#FFDEAD", "ヘルプ":"#D3D3D3"}

today = datetime.now()
monday = today - timedelta(days=today.weekday())

st.markdown('<div class="shift-table-wrapper">', unsafe_allow_html=True)

for i in range(7):
    d = monday + timedelta(days=i)
    is_hol = jpholiday.is_holiday(d)
    date_str = d.strftime('%m/%d')
    date_label = f"{date_str}({['月','火','水','木','金','土','日'][d.weekday()]})"

    # スプレッドシートからその日のREC(75列目)とLIVE(76列目)を取得
    rec_val, live_val = "", ""
    if df_sheet is not None:
        for _, row in df_sheet.iterrows():
            if date_str in str(row[0]):
                rec_val = row[74] if len(row) > 74 else ""
                live_val = row[75] if len(row) > 75 else ""
                break

    # ヘッダー
    h_html = '<div class="grid-container"><div class="cell header">日付</div><div class="cell header">名前</div>'
    for hr in range(7, 31): h_html += f'<div class="cell header hour-marker" style="grid-column: span 2;">{hr if hr < 24 else hr-24}</div>'
    h_html += '<div class="cell header">予定</div><div class="cell header">REC</div><div class="cell header">LIVE</div></div>'
    st.markdown(h_html, unsafe_allow_html=True)

    # スタッフ行
    body = '<div class="grid-container">'
    for idx, name in enumerate(staff_list):
        # 日付セル (最初の行だけ表示)
        date_bg = "holiday-bg" if is_hol else ""
        body += f'<div class="cell {date_bg}" style="grid-row: span 1;">{date_label if idx==0 else ""}</div>'
        # 名前セル
        body += f'<div class="cell staff-cell" style="background-color:{staff_colors.get(name, "#fff")}">{name}</div>'
        # シフトマス (48マス)
        for m in range(48):
            body += f'<div class="cell {"hour-marker" if m % 2 == 1 else ""}"></div>'
        # 予定・REC・LIVE (最初の行に結合表示)
        if idx == 0:
            body += f'<div class="cell" style="grid-row: span {len(staff_list)};"></div>' # 予定
            body += f'<div class="cell" style="grid-row: span {len(staff_list)}; color:red; font-weight:bold;">{rec_val}</div>'
            body += f'<div class="cell" style="grid-row: span {len(staff_list)}; color:blue; font-weight:bold;">{live_val}</div>'
    
    body += '</div><div style="height:10px;"></div>'
    st.markdown(body, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)
