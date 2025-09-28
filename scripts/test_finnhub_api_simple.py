#!/usr/bin/env python3
"""
Finnhub API 간단 테스트 스크립트 (한글 이모지 제거)
"""

import requests
import json
import time
from datetime import datetime, timedelta

# Finnhub API 키
FINNHUB_API_KEY = "d3bpft1r01qqg7bvjb4gd3bpft1r01qqg7bvjb50"

def test_finnhub_connection():
    """Finnhub API 연결 테스트"""
    
    print("Finnhub API 연결 테스트 시작...")
    print(f"API Key: {FINNHUB_API_KEY[:10]}...{FINNHUB_API_KEY[-5:]}")
    
    base_url = "https://finnhub.io/api/v1"
    
    # 1. 주식 실시간 가격 테스트
    print("\n1. AAPL 주식 가격 테스트")
    try:
        url = f"{base_url}/quote"
        params = {"symbol": "AAPL", "token": FINNHUB_API_KEY}
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'c' in data:  # current price
                print(f"성공: AAPL 현재가 ${data['c']}")
                print(f"변동: ${data.get('d', 0)} ({data.get('dp', 0)}%)")
                return True
            else:
                print(f"경고: 응답 데이터 이상 {data}")
                return False
        else:
            print(f"실패: API 호출 실패 {response.status_code}")
            return False
            
    except Exception as e:
        print(f"오류: {e}")
        return False

def save_test_data():
    """테스트 데이터 저장"""
    print("\n샘플 데이터 수집 중...")
    
    sample_stocks = ['AAPL', 'GOOGL', 'MSFT']
    sample_data = {}
    
    for symbol in sample_stocks:
        try:
            url = f"https://finnhub.io/api/v1/quote"
            params = {"symbol": symbol, "token": FINNHUB_API_KEY}
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                sample_data[symbol] = {
                    'current_price': data.get('c'),
                    'change': data.get('d'),
                    'percent_change': data.get('dp'),
                    'timestamp': datetime.now().isoformat()
                }
                print(f"{symbol} 데이터 수집 완료")
            
            time.sleep(1)
            
        except Exception as e:
            print(f"{symbol} 실패: {e}")
    
    # 데이터 저장
    if sample_data:
        with open("C:/project/Fin-Hub/data/finnhub_test_data.json", 'w') as f:
            json.dump(sample_data, f, indent=2)
        print("테스트 데이터 저장 완료")

if __name__ == "__main__":
    success = test_finnhub_connection()
    if success:
        save_test_data()
        print("\nFinnhub API 테스트 성공!")
    else:
        print("\nFinnhub API 테스트 실패!")