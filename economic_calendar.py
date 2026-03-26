import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime

# 1. 설정: 경제 일정 채널 전용 웹훅
DISCORD_WEBHOOK_URL = os.environ.get('CALENDAR_WEBHOOK')

def get_economic_calendar():
    # Investing.com의 경제 캘린더 (한국어 설정)
    url = "https://ko.investing.com/economic-calendar/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 오늘 날짜의 이벤트 행(row) 찾기
        table = soup.find('table', id='economicCalendarData')
        rows = table.find_all('tr', class_='js-event-item')
        
        events = []
        for row in rows:
            # 중요도 확인 (별 3개인 것만 필터링)
            sentiment = row.find('td', class_='sentiment')
            bull_icons = sentiment.find_all('i', class_='grayFullBullishIcon')
            
            if len(bull_icons) >= 3: # 중요도 '높음'만 선택
                time = row.find('td', class_='time').text.strip()
                currency = row.find('td', class_='left flagCur').text.strip()
                event_name = row.find('td', class_='event').text.strip()
                
                # 미국(USD)과 한국(KRW) 위주로 필터링 (선택 사항)
                if currency in ["USD", "KRW"]:
                    events.append(f"⏰ `{time}` **[{currency}]** {event_name}")
        
        return events
    except Exception as e:
        print(f"❌ 캘린더 크롤링 오류: {e}")
        return []

def send_to_discord():
    events = get_economic_calendar()
    
    if not events:
        content = "📅 오늘 예정된 주요(별 3개) 경제 일정이 없습니다."
    else:
        content = "\n".join(events)

    payload = {
        "embeds": [{
            "title": "🗓️ 오늘의 주요 경제 일정 (중요도: 高)",
            "description": content,
            "color": 15844367, # 골드 색상
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {"text": "주린이 계산기 - 경제 기상 예보"}
        }]
    }
    
    requests.post(DISCORD_WEBHOOK_URL, json=payload)

if __name__ == "__main__":
    send_to_discord()