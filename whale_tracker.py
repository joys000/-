import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime

# 설정: 고래 알림 전용 웹훅
DISCORD_WEBHOOK_URL = os.environ.get('WHALE_WEBHOOK')

def get_insider_trading():
    # OpenInsider: 최근 내부자 매수(Cluster Purchase) 페이지
    url = "http://openinsider.com/insider-transactions-25k"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        table = soup.find('table', class_='tinytable')
        if not table: return []
        
        rows = table.find_all('tr')[1:6] # 최신 5건만 추출
        trades = []
        
        for row in rows:
            cols = row.find_all('td')
            if len(cols) < 10: continue
            
            ticker = cols[3].text.strip() # 티커
            insider = cols[4].text.strip() # 이름
            title = cols[5].text.strip() # 직함
            trade_type = cols[7].text.strip() # 매수/매도
            price = cols[8].text.strip() # 가격
            value = cols[10].text.strip() # 총 거래 금액
            
            # 'P - Purchase' (매수)인 경우만 강조
            if "P - Purchase" in trade_type:
                trades.append({
                    "ticker": ticker,
                    "info": f"👤 **{insider}** ({title})\n💰 거래액: **{value}**\n💵 가격: {price}"
                })
        return trades
    except Exception as e:
        print(f"❌ 고래 추적 오류: {e}")
        return []

def send_to_discord():
    trades = get_insider_trading()
    if not trades: return

    embeds = []
    for trade in trades:
        embeds.append({
            "title": f"🚀 내부자 집중 매수 포착: {trade['ticker']}",
            "description": trade['info'],
            "color": 3066993, # 초록색 (매수 신호)
            "footer": {"text": "주린이 계산기 - 세력 추적 시스템"}
        })

    payload = {"embeds": embeds}
    requests.post(DISCORD_WEBHOOK_URL, json=payload)

if __name__ == "__main__":
    send_to_discord()