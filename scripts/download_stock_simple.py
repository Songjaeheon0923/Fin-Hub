#!/usr/bin/env python3
"""
주식 데이터 다운로드 스크립트 (간단 버전)
"""

import yfinance as yf
import pandas as pd
import os
import time
from datetime import datetime, timedelta
import json

def download_stock_data():
    """주요 주식 데이터 다운로드"""
    
    print("주식 데이터 다운로드 시작...")
    
    # 데이터 저장 디렉토리
    data_dir = "C:/project/Fin-Hub/data/stock-data"
    os.makedirs(data_dir, exist_ok=True)
    
    # 주요 종목들 (처음 30개)
    major_stocks = [
        'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'TSLA', 'META', 'NVDA', 'JPM', 'JNJ',
        'V', 'WMT', 'PG', 'UNH', 'HD', 'MA', 'DIS', 'PYPL', 'BAC', 'NFLX',
        'ADBE', 'CRM', 'CMCSA', 'XOM', 'VZ', 'KO', 'ABT', 'NKE', 'T', 'TMO'
    ]
    
    print(f"{len(major_stocks)}개 주요 종목 다운로드 예정")
    
    # 날짜 설정 (최근 1년 데이터)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    print(f"데이터 기간: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
    
    successful_downloads = 0
    failed_symbols = []
    download_info = []
    
    for i, symbol in enumerate(major_stocks):
        try:
            print(f"다운로드 중: {symbol} [{i+1}/{len(major_stocks)}]")
            
            # yfinance로 주가 데이터 다운로드
            stock = yf.Ticker(symbol)
            
            # 과거 데이터 가져오기
            hist_data = stock.history(start=start_date, end=end_date, interval="1d")
            
            if not hist_data.empty and len(hist_data) > 50:  # 최소 50일 데이터
                # 인덱스를 문자열로 변환
                hist_data.index = hist_data.index.strftime('%Y-%m-%d')
                
                # CSV로 저장
                csv_file = os.path.join(data_dir, f"{symbol}.csv")
                hist_data.to_csv(csv_file)
                
                # 기본 정보 수집
                try:
                    info = stock.info
                    stock_info = {
                        'symbol': symbol,
                        'name': info.get('longName', 'N/A'),
                        'sector': info.get('sector', 'N/A'),
                        'market_cap': info.get('marketCap', 0),
                        'data_points': len(hist_data),
                        'date_range': {
                            'start': hist_data.index[0],
                            'end': hist_data.index[-1]
                        }
                    }
                except:
                    stock_info = {
                        'symbol': symbol,
                        'name': 'N/A',
                        'sector': 'N/A',
                        'market_cap': 0,
                        'data_points': len(hist_data),
                        'date_range': {
                            'start': hist_data.index[0],
                            'end': hist_data.index[-1]
                        }
                    }
                
                download_info.append(stock_info)
                successful_downloads += 1
                print(f"{symbol} 데이터 저장 완료 ({len(hist_data)}일)")
                
            else:
                print(f"{symbol} 데이터 부족 (건너뜀)")
                failed_symbols.append(symbol)
            
            # API 호출 제한
            time.sleep(0.2)
            
        except Exception as e:
            print(f"{symbol} 다운로드 실패: {e}")
            failed_symbols.append(symbol)
            time.sleep(1)
    
    # 메타데이터 저장
    metadata = {
        'download_date': datetime.now().isoformat(),
        'data_source': 'Yahoo Finance (yfinance)',
        'total_symbols_requested': len(major_stocks),
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
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n다운로드 완료:")
    print(f"성공: {successful_downloads}개")
    print(f"실패: {len(failed_symbols)}개")
    print(f"메타데이터: {metadata_file}")
    
    if failed_symbols:
        print(f"실패 목록: {', '.join(failed_symbols)}")
    
    print("주식 데이터 다운로드 완료!")

if __name__ == "__main__":
    download_stock_data()