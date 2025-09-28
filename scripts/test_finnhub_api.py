#!/usr/bin/env python3
"""
Finnhub API 테스트 스크립트
발급받은 API 키가 정상 작동하는지 확인
"""

import requests
import json
import time
from datetime import datetime, timedelta

# Finnhub API 키
FINNHUB_API_KEY = "d3bpft1r01qqg7bvjb4gd3bpft1r01qqg7bvjb50"

def test_finnhub_connection():
    """Finnhub API 연결 테스트"""
    
    print("🔑 Finnhub API 연결 테스트 시작...")
    print(f"API Key: {FINNHUB_API_KEY[:10]}...{FINNHUB_API_KEY[-5:]}")
    
    base_url = "https://finnhub.io/api/v1"
    
    test_results = {}
    
    # 1. 주식 실시간 가격 테스트
    print("\n📊 1. 주식 실시간 가격 테스트 (AAPL)")
    try:
        url = f"{base_url}/quote"
        params = {"symbol": "AAPL", "token": FINNHUB_API_KEY}
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'c' in data:  # current price
                print(f"✅ AAPL 현재가: ${data['c']}")
                print(f"   변동: ${data.get('d', 0)} ({data.get('dp', 0)}%)")
                test_results['stock_quote'] = True
            else:
                print(f"⚠️ 응답 데이터 이상: {data}")
                test_results['stock_quote'] = False
        else:
            print(f"❌ API 호출 실패: {response.status_code}")
            test_results['stock_quote'] = False
            
    except Exception as e:
        print(f"❌ 주식 가격 테스트 실패: {e}")
        test_results['stock_quote'] = False
    
    time.sleep(1)
    
    # 2. 회사 프로필 테스트
    print("\n🏢 2. 회사 프로필 테스트 (AAPL)")
    try:
        url = f"{base_url}/stock/profile2"
        params = {"symbol": "AAPL", "token": FINNHUB_API_KEY}
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'name' in data:
                print(f"✅ 회사명: {data.get('name')}")
                print(f"   업종: {data.get('finnhubIndustry')}")
                print(f"   시가총액: ${data.get('marketCapitalization', 0):,}M")
                test_results['company_profile'] = True
            else:
                print(f"⚠️ 회사 프로필 데이터 없음: {data}")
                test_results['company_profile'] = False
        else:
            print(f"❌ 회사 프로필 API 호출 실패: {response.status_code}")
            test_results['company_profile'] = False
            
    except Exception as e:
        print(f"❌ 회사 프로필 테스트 실패: {e}")
        test_results['company_profile'] = False
    
    time.sleep(1)
    
    # 3. 뉴스 데이터 테스트
    print("\n📰 3. 뉴스 데이터 테스트 (AAPL)")
    try:
        # 최근 7일 뉴스
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        url = f"{base_url}/company-news"
        params = {
            "symbol": "AAPL",
            "from": start_date.strftime('%Y-%m-%d'),
            "to": end_date.strftime('%Y-%m-%d'),
            "token": FINNHUB_API_KEY
        }
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            news_data = response.json()
            if isinstance(news_data, list) and len(news_data) > 0:
                print(f"✅ 뉴스 {len(news_data)}개 조회 완료")
                print(f"   최신 뉴스: {news_data[0].get('headline', 'N/A')[:60]}...")
                test_results['company_news'] = True
            else:
                print(f"⚠️ 뉴스 데이터 없음")
                test_results['company_news'] = False
        else:
            print(f"❌ 뉴스 API 호출 실패: {response.status_code}")
            test_results['company_news'] = False
            
    except Exception as e:
        print(f"❌ 뉴스 테스트 실패: {e}")
        test_results['company_news'] = False
    
    time.sleep(1)
    
    # 4. 기술적 지표 테스트 (RSI)
    print("\n📈 4. 기술적 지표 테스트 (RSI)")
    try:
        url = f"{base_url}/indicator"
        params = {
            "symbol": "AAPL",
            "resolution": "D",
            "from": int((datetime.now() - timedelta(days=100)).timestamp()),
            "to": int(datetime.now().timestamp()),
            "indicator": "rsi",
            "timeperiod": 14,
            "token": FINNHUB_API_KEY
        }
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            rsi_data = response.json()
            if 'rsi' in rsi_data and len(rsi_data['rsi']) > 0:
                latest_rsi = rsi_data['rsi'][-1]
                print(f"✅ RSI (14일): {latest_rsi:.2f}")
                test_results['technical_indicator'] = True
            else:
                print(f"⚠️ RSI 데이터 없음: {rsi_data}")
                test_results['technical_indicator'] = False
        else:
            print(f"❌ 기술적 지표 API 호출 실패: {response.status_code}")
            test_results['technical_indicator'] = False
            
    except Exception as e:
        print(f"❌ 기술적 지표 테스트 실패: {e}")
        test_results['technical_indicator'] = False
    
    # 결과 요약
    print("\n🎯 Finnhub API 테스트 결과:")
    for test_name, result in test_results.items():
        status = "✅ 성공" if result else "❌ 실패"
        print(f"   {test_name}: {status}")
    
    success_rate = sum(test_results.values()) / len(test_results) * 100
    print(f"\n📊 전체 성공률: {success_rate:.1f}%")
    
    if success_rate >= 75:
        print("🎉 Finnhub API 연결 성공! 대부분의 기능이 정상 작동합니다.")
    elif success_rate >= 50:
        print("⚠️ Finnhub API 부분적 성공. 일부 기능에 제한이 있을 수 있습니다.")
    else:
        print("❌ Finnhub API 연결 실패. API 키나 네트워크 연결을 확인해주세요.")
    
    return test_results

def save_sample_data():
    """샘플 데이터 저장"""
    print("\n💾 샘플 데이터 저장 중...")
    
    sample_stocks = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN']
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
                    'high': data.get('h'),
                    'low': data.get('l'),
                    'open': data.get('o'),
                    'previous_close': data.get('pc'),
                    'timestamp': datetime.now().isoformat()
                }
                print(f"✅ {symbol} 데이터 수집 완료")
            
            time.sleep(0.5)  # API 레이트 리미팅
            
        except Exception as e:
            print(f"❌ {symbol} 데이터 수집 실패: {e}")
    
    # 샘플 데이터 저장
    if sample_data:
        sample_file = "C:/project/Fin-Hub/data/finnhub_sample_data.json"
        with open(sample_file, 'w', encoding='utf-8') as f:
            json.dump(sample_data, f, indent=2, ensure_ascii=False)
        print(f"💾 샘플 데이터 저장: {sample_file}")

if __name__ == "__main__":
    test_results = test_finnhub_connection()
    save_sample_data()
    print("\n🔧 Finnhub API 테스트 완료!")