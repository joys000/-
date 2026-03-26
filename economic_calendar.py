import requests
import os
from datetime import datetime
import pandas as pd

# 1. 설정: 경제 일정 채널 전용 웹훅
DISCORD_WEBHOOK_URL = os.environ.get('CALENDAR_WEBHOOK')

def get_economic_calendar():
    # Yahoo Finance 경제 캘린더 (더 안정적임)
    url = "https://finance.yahoo.com/calendar/economic/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
    }
    
    try:
        # 야후 파이낸스는 pandas로도 쉽게 긁어올 수 있습니다.
        response = requests.get(url, headers=headers)
        tables = pd.read_html(response.text)
        
        if not tables:
            return []
            
        df = tables[0] # 첫 번째 테이블 선택
        
        # 컬럼명 확인 및 필터링
        # 컬럼명: 'Time', 'Country', 'Event', 'Actual', 'Expected', 'Prior'
        events = []
        for index, row in df.iterrows():
            # 미국(United States)과 한국(South Korea) 일정만 추출
            if row['Country'] in ['United States', 'South Korea']:
                time = row['Time']
                country = "🇺🇸" if row['Country'] == 'United States' else "🇰🇷"
                event = row['Event']
                events.append(f"⏰ `{time}` {country} {event}")
        
        return events[:10] # 너무 많으면 상위 10개만
    except Exception as e:
        print(f"❌ 캘린더 데이터 로딩 실패: {e}")
        return []

def send_to_discord():
    if not DISCORD_WEBHOOK_URL:
        print("❌ 에러: CALENDAR_WEBHOOK 환경변수가 없습니다.")
        return

    events = get_economic_calendar()
    
    if not events:
        content = "📅 오늘 예정된 주요 경제 일정이 없거나 데이터를 가져오지 못했습니다."
    else:
        content = "\n".join(events)

    payload = {
        "embeds": [{
            "title": "🗓️ 오늘의 주요 글로벌 경제 일정",
            "description": content,
            "color": 15844367, # 골드
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {"text": "주린이 계산기 - 글로벌 매크로 브리핑"}
        }]
    }
    
    requests.post(DISCORD_WEBHOOK_URL, json=payload)
    print("✅ 캘린더 전송 성공!")

if __name__ == "__main__":
    send_to_discord()
