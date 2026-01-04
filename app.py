import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
import jpholiday

st.set_page_config(layout="wide")

# CSSでレイアウト崩れを強制防止
st.markdown("""
<style>
    .shift-container { overflow-x: auto; white-space: nowrap; border: 1px solid #333; padding: 10px; }
    .grid { display: grid; grid-template-columns: 80px 100px repeat(48, 20px) 100px; width: fit-content; }
    .c { border: 0.1px solid #ddd; height: 30px; line-height: 30px; text-align: center; font-size: 11px; background: white; }
    .h { background: #333; color: white; font-weight: bold; }
    .staff-name { font-weight: bold; background: #f0f2f6; border-right: 2px solid #333; }
</style>
""", unsafe_allow_html=True)

# 認証
def get_client():
    try:
        creds_dict = {
            "type": "service_account",
            "project_id": "dauntless-motif-294307",
            "private_key_id": "51309e4d6320e1bb0748ce1f5a6c886e44c5cabc",
            "private_key": st.secrets["PRIVATE_KEY"], # Secretsから呼ぶ
            "client_email": "west-shift-app@dauntless-motif-294307.iam.gserviceaccount.com",
            "client_id": "114530383906045619062",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/west-shift-app%40dauntless-motif-294307.iam.gserviceaccount.com"
        }
        return gspread.authorize(ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]))
    except Exception as e:
        st.error(f"認証エラー: {e}")
        return None

client = get_client()
if client:
    st.sidebar.success("接続完了")
    # ここにシート読み込み処理を書く

# シフト表表示
st.title("週間シフト管理")
staff_list = ["内村", "片岡", "久保田", "足立", "松田", "広我", "ニコ", "紗希", "ジョン", "米田", "難波", "ヘルプ"]

st.markdown('<div class="shift-container">', unsafe_allow_html=True)
# ヘッダー
header = '<div class="grid"><div class="c h">日付</div><div class="c h">名前</div>'
for i in range(7, 31): header += f'<div class="c h" style="grid-column: span 2;">{i if i < 24 else i-24}</div>'
st.markdown(header + '</div>', unsafe_allow_html=True)

# 1日分の描画
today = datetime.now()
monday = today - timedelta(days=today.weekday())
for i in range(7):
    d = monday + timedelta(days=i)
    day_html = f'<div class="grid"><div class="c" style="grid-row: span {len(staff_list)};">{d.strftime("%m/%d")}</div>'
    for name in staff_list:
        day_html += f'<div class="c staff-name">{name}</div>'
        for _ in range(48): day_html += '<div class="c"></div>'
        day_html += '<div class="c"></div>' # 予定
    st.markdown(day_html + '</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)
