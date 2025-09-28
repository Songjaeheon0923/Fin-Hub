#!/usr/bin/env python3
"""
주식 데이터 다운로드 스크립트
yfinance를 사용하여 S&P 500 종목들의 과거 데이터를 다운로드
"""

import yfinance as yf
import pandas as pd
import os
import time
from datetime import datetime, timedelta
import json

def get_sp500_symbols():
    """S&P 500 종목 심볼 리스트 가져오기"""
    try:
        # Wikipedia에서 S&P 500 종목 리스트 가져오기
        url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        tables = pd.read_html(url)
        sp500_table = tables[0]
        symbols = sp500_table['Symbol'].tolist()
        
        # 일부 심볼 정리 (점이 포함된 경우 하이픈으로 변경)
        cleaned_symbols = []
        for symbol in symbols:
            if '.' in symbol:
                symbol = symbol.replace('.', '-')
            cleaned_symbols.append(symbol)
        
        return cleaned_symbols
    except Exception as e:
        print(f"❌ S&P 500 리스트 가져오기 실패: {e}")
        # 백업용 주요 종목들
        return ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'JPM', 'JNJ', 'V',
                'WMT', 'PG', 'UNH', 'HD', 'MA', 'DIS', 'PYPL', 'BAC', 'NFLX', 'ADBE',
                'CRM', 'CMCSA', 'XOM', 'VZ', 'KO', 'ABT', 'NKE', 'T', 'TMO', 'COST']

def download_stock_data():
    """S&P 500 주식 데이터 다운로드"""
    
    print("🚀 S&P 500 주식 데이터 다운로드 시작...")
    
    # 데이터 저장 디렉토리
    data_dir = "C:/project/Fin-Hub/data/stock-data"
    os.makedirs(data_dir, exist_ok=True)
    
    # S&P 500 종목 리스트 가져오기
    print("📋 S&P 500 종목 리스트 가져오는 중...")
    symbols = get_sp500_symbols()
    print(f"✅ {len(symbols)}개 종목 리스트 조회 완료")
    
    # 날짜 설정 (최근 2년 데이터로 제한하여 용량 절약)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=2*365)  # 2년 데이터
    
    print(f"📅 데이터 기간: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
    
    successful_downloads = 0
    failed_symbols = []
    download_info = []
    
    # 첫 100개 종목만 다운로드 (용량 제한)
    symbols_to_download = symbols[:100]
    
    for i, symbol in enumerate(symbols_to_download):
        try:
            print(f"📊 다운로드 중: {symbol} [{i+1}/{len(symbols_to_download)}]")
            
            # yfinance로 주가 데이터 다운로드
            stock = yf.Ticker(symbol)
            
            # 기본 정보 가져오기
            info = stock.info
            
            # 과거 데이터 가져오기
            hist_data = stock.history(start=start_date, end=end_date, interval="1d")
            
            if not hist_data.empty and len(hist_data) > 100:  # 최소 100일 데이터가 있어야 함
                # 데이터 정리
                hist_data.index = hist_data.index.strftime('%Y-%m-%d')
                
                # CSV로 저장
                csv_file = os.path.join(data_dir, f"{symbol}.csv")
                hist_data.to_csv(csv_file)
                
                # 종목 정보 저장
                stock_info = {
                    'symbol': symbol,
                    'name': info.get('longName', 'N/A'),
                    'sector': info.get('sector', 'N/A'),
                    'industry': info.get('industry', 'N/A'),
                    'market_cap': info.get('marketCap', 0),
                    'employees': info.get('fullTimeEmployees', 0),
                    'website': info.get('website', 'N/A'),
                    'business_summary': info.get('businessSummary', 'N/A')[:500],  # 500자로 제한
                    'data_points': len(hist_data),
                    'date_range': {
                        'start': hist_data.index[0],
                        'end': hist_data.index[-1]
                    }
                }
                download_info.append(stock_info)
                
                successful_downloads += 1
                print(f"✅ {symbol} 데이터 저장 완료 ({len(hist_data)}일 데이터)")
                
            else:
                print(f"⚠️ {symbol} 데이터 부족 (건너뜀)")
                failed_symbols.append(symbol)
            
            # API 호출 제한 준수
            time.sleep(0.1)
            
        except Exception as e:
            print(f"❌ {symbol} 다운로드 실패: {e}")
            failed_symbols.append(symbol)
            time.sleep(0.5)
    
    # 종목 정보 메타데이터 저장
    metadata = {
        'download_date': datetime.now().isoformat(),
        'data_source': 'Yahoo Finance (yfinance)',
        'total_symbols_requested': len(symbols_to_download),
        'successful_downloads': successful_downloads,
        'failed_downloads': len(failed_symbols),
        'failed_symbols': failed_symbols,
        'data_period_days': (end_date - start_date).days,
        'date_range': {
            'start': start_date.strftime('%Y-%m-%d'),
            'end': end_date.strftime('%Y-%m-%d')
        },
        'stocks_info': download_info
    }
    
    metadata_file = os.path.join(data_dir, "_metadata.json")
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    # 결과 요약
    print("\n📈 다운로드 완료 요약:")
    print(f"✅ 성공: {successful_downloads}개")
    print(f"❌ 실패: {len(failed_symbols)}개")
    print(f"💾 메타데이터 저장: {metadata_file}")
    
    if failed_symbols:
        print(f"실패 목록: {', '.join(failed_symbols[:10])}{'...' if len(failed_symbols) > 10 else ''}")
    
    print("🎉 주식 데이터 다운로드 완료!")

if __name__ == "__main__":
    download_stock_data()