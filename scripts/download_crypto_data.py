#!/usr/bin/env python3
"""
암호화폐 데이터 다운로드 스크립트
CoinGecko API를 사용하여 상위 100개 암호화폐의 1년 데이터를 다운로드
"""

import requests
import json
import time
import os
from datetime import datetime, timedelta
import pandas as pd

def download_crypto_data():
    """상위 100개 암호화폐 데이터 다운로드"""
    
    print("🚀 암호화폐 데이터 다운로드 시작...")
    
    # 데이터 저장 디렉토리
    cache_dir = "C:/project/Fin-Hub/data/crypto-cache"
    os.makedirs(cache_dir, exist_ok=True)
    
    # 상위 100개 암호화폐 리스트 가져오기
    print("📋 상위 100개 암호화폐 리스트 가져오는 중...")
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        'vs_currency': 'usd',
        'order': 'market_cap_desc',
        'per_page': 100,
        'page': 1,
        'sparkline': 'false'
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        coins = response.json()
        print(f"✅ {len(coins)}개 코인 리스트 조회 완료")
    except Exception as e:
        print(f"❌ 코인 리스트 조회 실패: {e}")
        return
    
    # 현재 시장 데이터 저장
    market_data_file = os.path.join(cache_dir, "market_overview.json")
    with open(market_data_file, 'w', encoding='utf-8') as f:
        json.dump(coins, f, indent=2, ensure_ascii=False)
    print(f"💾 시장 개요 데이터 저장: {market_data_file}")
    
    # 각 코인별 상세 데이터 다운로드
    successful_downloads = 0
    failed_downloads = []
    
    for i, coin in enumerate(coins[:50]):  # 처음 50개만 다운로드 (API 레이트 리미팅 고려)
        coin_id = coin['id']
        coin_name = coin['name']
        
        print(f"📊 다운로드 중: {coin_name} ({coin_id}) [{i+1}/50]")
        
        try:
            # 1년 가격 데이터
            history_url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
            history_params = {
                'vs_currency': 'usd',
                'days': 365,
                'interval': 'daily'
            }
            
            history_response = requests.get(history_url, params=history_params, timeout=15)
            history_response.raise_for_status()
            history_data = history_response.json()
            
            # 데이터 처리 및 저장
            processed_data = {
                'coin_info': {
                    'id': coin_id,
                    'name': coin_name,
                    'symbol': coin['symbol'].upper(),
                    'current_price': coin.get('current_price'),
                    'market_cap': coin.get('market_cap'),
                    'market_cap_rank': coin.get('market_cap_rank'),
                    'total_volume': coin.get('total_volume'),
                    'price_change_24h': coin.get('price_change_24h'),
                    'price_change_percentage_24h': coin.get('price_change_percentage_24h'),
                    'last_updated': coin.get('last_updated')
                },
                'price_history': history_data
            }
            
            # JSON 파일로 저장
            file_path = os.path.join(cache_dir, f"{coin_id}_data.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(processed_data, f, indent=2, ensure_ascii=False)
            
            successful_downloads += 1
            print(f"✅ {coin_name} 데이터 저장 완료")
            
            # API 레이트 리미팅 준수 (1초 대기)
            time.sleep(1.2)
            
        except Exception as e:
            print(f"❌ {coin_name} 다운로드 실패: {e}")
            failed_downloads.append(coin_id)
            time.sleep(2)  # 오류시 더 긴 대기
    
    # 결과 요약
    print("\n📈 다운로드 완료 요약:")
    print(f"✅ 성공: {successful_downloads}개")
    print(f"❌ 실패: {len(failed_downloads)}개")
    if failed_downloads:
        print(f"실패 목록: {', '.join(failed_downloads)}")
    
    # 메타데이터 저장
    metadata = {
        'download_date': datetime.now().isoformat(),
        'total_coins_requested': 50,
        'successful_downloads': successful_downloads,
        'failed_downloads': failed_downloads,
        'data_source': 'CoinGecko API',
        'data_period': '365 days',
        'currency': 'USD'
    }
    
    metadata_file = os.path.join(cache_dir, "_metadata.json")
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    print(f"💾 메타데이터 저장: {metadata_file}")
    print("🎉 암호화폐 데이터 다운로드 완료!")

if __name__ == "__main__":
    download_crypto_data()