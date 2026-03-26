import requests
from bs4 import BeautifulSoup
import os
import json
from datetime import datetime

# 1. 설정: 디스코드 웹훅 & 백엔드 서버 주소
DISCORD_WEBHOOK_URL = os.environ.get('WHALE_WEBHOOK')
SERVER_URL = "https://dividend-server.onrender.com/update_whales"

def clean_value(value_str):
    """$1,234,567 형태의 문자열을 숫자로 변환"""
    try:
        return int(value_str.replace('$', '').replace(',', '').replace('+', ''))
    except:
        return 0

def get_insider_trading():
    # OpenInsider: 최근 내부자 매수(Cluster Purchase) 페이지
    url = "http://openinsider.com/insider-transactions-25k"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        table = soup.find('table', class_='tinytable')
        if not table: return []
        
        rows = table.find_all('tr')[1:15] # 필터링을 위해 15개 정도로 넉넉히 가져옴
        trades = []
        
        for row in rows:
            cols = row.find_all('td')
            if len(cols) < 10: continue
            
            trade_type = cols[7].text.strip() # 매수/매도
            value_raw = cols[10].text.strip() # 총 거래 금액 (예: +$1,234,567)
            value_num = clean_value(value_raw)

            # 🚨 조건: 'P - Purchase'(매수) 이면서 거래액이 $1,000,000 이상인 경우만!
            if "P - Purchase" in trade_type and value_num >= 1000000:
                ticker = cols[3].text.strip()
                insider = cols[4].text.strip()
                title = cols[5].text.strip()
                price = cols[8].text.strip()
                trade_date = cols[1].text.strip() # 거래 날짜

                trades.append({
                    "symbol": ticker,
                    "owner": insider,
                    "title": title,
                    "value": value_raw,
                    "price": price,
                    "date": trade_date,
                    "type": "WHALE"
                })
        
        return trades
    except Exception as e:
        print(f"❌ 고래 추적 오류: {e}")
        return []

def send_to_server(trade):
    """우리 FastAPI 서버로 데이터 전송"""
    try:
        # Render 서버가 자고 있을 수 있으므로 timeout을 넉넉히 줌
        res = requests.post(SERVER_URL, json=trade, timeout=15)
        if res.status_code == 200:
            print(f"✅ 서버 전송 성공: {trade['symbol']}")
        else:
            print(f"⚠️ 서버 응답 에러 ({res.status_code}): {trade['symbol']}")
    except Exception as e:
        print(f"❌ 서버 연결 실패 (서버가 자는 중일 가능성 높음): {e}")

def run_tracker():
    trades = get_insider_trading()
    if not trades:
        print("🔍 조건에 맞는 고래 거래가 없습니다.")
        return

    embeds = []
    for trade in trades:
        # 1. 서버로 데이터 쏘기 (웹사이트 표시용)
        send_to_server(trade)

        # 2. 디스코드용 데이터 쌓기
        embeds.append({
            "title": f"🐋 초대형 고래 포착: {trade['symbol']}",
            "description": f"👤 **{trade['owner']}** ({trade['title']})\n💰 거래액: **{trade['value']}**\n💵 가격: {trade['price']}\n📅 날짜: {trade['date']}",
            "color": 3066993,
            "footer": {"text": "주린이 인텔리전스 - 세력 감시 시스템"}
        })

    # 3. 디스코드 전송
    if embeds:
        payload = {"embeds": embeds[:10]} # 디코 제한상 최대 10개만
        requests.post(DISCORD_WEBHOOK_URL, json=payload)
        print(f"📢 디스코드 알림 전송 완료! ({len(embeds)}건)")

if __name__ == "__main__":
    run_tracker()
