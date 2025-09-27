"""
Gekko 스타일 SQLite 대용량 데이터 캐시 시스템
21GB급 역사 데이터 효율적 관리
"""

import sqlite3
import pandas as pd
import numpy as np
import asyncio
import aiosqlite
import json
import gzip
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from contextlib import asynccontextmanager
import logging
from concurrent.futures import ThreadPoolExecutor
import hashlib
import os


logger = logging.getLogger(__name__)


@dataclass
class DataCacheConfig:
    """데이터 캐시 설정"""
    cache_dir: str = "data/cache"
    db_name: str = "market_data.db"
    max_db_size_gb: int = 5  # 단일 DB 최대 크기
    compression: bool = True
    auto_vacuum: bool = True
    wal_mode: bool = True
    cache_ttl_hours: int = 24
    chunk_size: int = 10000
    index_enabled: bool = True


@dataclass
class MarketDataPoint:
    """시장 데이터 포인트"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    symbol: str
    exchange: str
    timeframe: str


class DataCacheManager:
    """Gekko 스타일 데이터 캐시 관리자"""

    def __init__(self, config: DataCacheConfig):
        self.config = config
        self.cache_dir = Path(config.cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # 거래소별 DB 분리 (Gekko 방식)
        self.db_connections = {}
        self.executor = ThreadPoolExecutor(max_workers=4)

        # 메모리 캐시 (최근 데이터 빠른 접근)
        self.memory_cache = {}
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'inserts': 0,
            'size_mb': 0
        }

    async def initialize(self):
        """캐시 시스템 초기화"""
        logger.info("Initializing data cache system...")

        # 주요 거래소별 DB 생성
        exchanges = ['binance', 'coinbase', 'kraken', 'bitfinex', 'huobi',
                    'kucoin', 'gate', 'okex', 'bybit', 'ftx']

        for exchange in exchanges:
            await self._create_exchange_db(exchange)

        # 통계 추적 DB
        await self._create_stats_db()

        logger.info(f"Cache system initialized with {len(exchanges)} exchange DBs")

    async def _create_exchange_db(self, exchange: str):
        """거래소별 데이터베이스 생성"""
        db_path = self.cache_dir / f"{exchange}.db"

        async with aiosqlite.connect(str(db_path)) as db:
            # WAL 모드 활성화 (동시 읽기/쓰기 성능 향상)
            if self.config.wal_mode:
                await db.execute("PRAGMA journal_mode=WAL")

            # 자동 VACUUM 설정
            if self.config.auto_vacuum:
                await db.execute("PRAGMA auto_vacuum=INCREMENTAL")

            # 성능 최적화 설정
            await db.execute("PRAGMA synchronous=NORMAL")
            await db.execute("PRAGMA cache_size=10000")
            await db.execute("PRAGMA temp_store=memory")

            # 시간대별 테이블 생성
            timeframes = ['1m', '5m', '15m', '1h', '4h', '1d', '1w']
            for timeframe in timeframes:
                table_name = f"candles_{timeframe}"
                await db.execute(f"""
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        symbol TEXT NOT NULL,
                        timestamp INTEGER NOT NULL,
                        open REAL NOT NULL,
                        high REAL NOT NULL,
                        low REAL NOT NULL,
                        close REAL NOT NULL,
                        volume REAL NOT NULL,
                        data_hash TEXT,
                        created_at INTEGER DEFAULT (strftime('%s','now')),
                        UNIQUE(symbol, timestamp)
                    )
                """)

                # 성능 최적화 인덱스
                if self.config.index_enabled:
                    await db.execute(f"""
                        CREATE INDEX IF NOT EXISTS idx_{table_name}_symbol_time
                        ON {table_name}(symbol, timestamp)
                    """)
                    await db.execute(f"""
                        CREATE INDEX IF NOT EXISTS idx_{table_name}_timestamp
                        ON {table_name}(timestamp)
                    """)

            # 메타데이터 테이블
            await db.execute("""
                CREATE TABLE IF NOT EXISTS metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at INTEGER DEFAULT (strftime('%s','now'))
                )
            """)

            await db.commit()

    async def _create_stats_db(self):
        """통계 추적 데이터베이스 생성"""
        db_path = self.cache_dir / "stats.db"

        async with aiosqlite.connect(str(db_path)) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS cache_stats (
                    date TEXT PRIMARY KEY,
                    exchange TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    records_count INTEGER DEFAULT 0,
                    data_size_mb REAL DEFAULT 0,
                    last_updated INTEGER DEFAULT (strftime('%s','now'))
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS access_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp INTEGER DEFAULT (strftime('%s','now')),
                    exchange TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    duration_ms INTEGER DEFAULT 0
                )
            """)

            await db.commit()

    async def store_candles(self, exchange: str, symbol: str, timeframe: str,
                          candles: List[MarketDataPoint]) -> bool:
        """캔들 데이터 저장"""
        if not candles:
            return True

        try:
            db_path = self.cache_dir / f"{exchange}.db"
            table_name = f"candles_{timeframe}"

            async with aiosqlite.connect(str(db_path)) as db:
                # 배치 삽입을 위한 데이터 준비
                insert_data = []
                for candle in candles:
                    data_hash = self._generate_data_hash(candle)
                    insert_data.append((
                        symbol,
                        int(candle.timestamp.timestamp()),
                        candle.open,
                        candle.high,
                        candle.low,
                        candle.close,
                        candle.volume,
                        data_hash
                    ))

                # 배치 삽입 (UPSERT)
                await db.executemany(f"""
                    INSERT OR REPLACE INTO {table_name}
                    (symbol, timestamp, open, high, low, close, volume, data_hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, insert_data)

                await db.commit()

            # 메모리 캐시 업데이트
            cache_key = f"{exchange}:{symbol}:{timeframe}"
            self.memory_cache[cache_key] = candles[-100:]  # 최근 100개만 메모리에

            self.cache_stats['inserts'] += len(candles)

            logger.debug(f"Stored {len(candles)} candles for {exchange}:{symbol}:{timeframe}")
            return True

        except Exception as e:
            logger.error(f"Error storing candles: {e}")
            return False

    async def get_candles(self, exchange: str, symbol: str, timeframe: str,
                         start_time: Optional[datetime] = None,
                         end_time: Optional[datetime] = None,
                         limit: Optional[int] = None) -> List[MarketDataPoint]:
        """캔들 데이터 조회"""
        start_timestamp = datetime.now()

        # 메모리 캐시 확인
        cache_key = f"{exchange}:{symbol}:{timeframe}"
        if cache_key in self.memory_cache and not start_time and not end_time:
            self.cache_stats['hits'] += 1
            return self.memory_cache[cache_key][-limit:] if limit else self.memory_cache[cache_key]

        try:
            db_path = self.cache_dir / f"{exchange}.db"
            if not db_path.exists():
                return []

            table_name = f"candles_{timeframe}"
            query = f"SELECT symbol, timestamp, open, high, low, close, volume FROM {table_name} WHERE symbol = ?"
            params = [symbol]

            # 시간 필터 조건 추가
            if start_time:
                query += " AND timestamp >= ?"
                params.append(int(start_time.timestamp()))

            if end_time:
                query += " AND timestamp <= ?"
                params.append(int(end_time.timestamp()))

            query += " ORDER BY timestamp ASC"

            if limit:
                query += " LIMIT ?"
                params.append(limit)

            async with aiosqlite.connect(str(db_path)) as db:
                cursor = await db.execute(query, params)
                rows = await cursor.fetchall()

                candles = []
                for row in rows:
                    candle = MarketDataPoint(
                        symbol=row[0],
                        timestamp=datetime.fromtimestamp(row[1]),
                        open=row[2],
                        high=row[3],
                        low=row[4],
                        close=row[5],
                        volume=row[6],
                        exchange=exchange,
                        timeframe=timeframe
                    )
                    candles.append(candle)

                # 메모리 캐시 업데이트 (최근 데이터만)
                if len(candles) <= 1000:
                    self.memory_cache[cache_key] = candles

                self.cache_stats['misses'] += 1

                # 액세스 로그 기록
                duration_ms = (datetime.now() - start_timestamp).total_seconds() * 1000
                await self._log_access(exchange, symbol, timeframe, "SELECT", int(duration_ms))

                logger.debug(f"Retrieved {len(candles)} candles for {exchange}:{symbol}:{timeframe}")
                return candles

        except Exception as e:
            logger.error(f"Error retrieving candles: {e}")
            return []

    async def get_latest_candle(self, exchange: str, symbol: str, timeframe: str) -> Optional[MarketDataPoint]:
        """최신 캔들 데이터 조회"""
        candles = await self.get_candles(exchange, symbol, timeframe, limit=1)
        return candles[-1] if candles else None

    async def get_symbols_list(self, exchange: str, timeframe: str = "1d") -> List[str]:
        """거래소의 사용 가능한 심볼 목록 조회"""
        try:
            db_path = self.cache_dir / f"{exchange}.db"
            if not db_path.exists():
                return []

            table_name = f"candles_{timeframe}"

            async with aiosqlite.connect(str(db_path)) as db:
                cursor = await db.execute(f"SELECT DISTINCT symbol FROM {table_name} ORDER BY symbol")
                rows = await cursor.fetchall()
                return [row[0] for row in rows]

        except Exception as e:
            logger.error(f"Error getting symbols list: {e}")
            return []

    async def cleanup_old_data(self, days_to_keep: int = 90):
        """오래된 데이터 정리"""
        cutoff_timestamp = int((datetime.now() - timedelta(days=days_to_keep)).timestamp())

        for db_file in self.cache_dir.glob("*.db"):
            if db_file.name == "stats.db":
                continue

            try:
                async with aiosqlite.connect(str(db_file)) as db:
                    timeframes = ['1m', '5m', '15m', '1h', '4h', '1d', '1w']
                    for timeframe in timeframes:
                        table_name = f"candles_{timeframe}"

                        # 1분, 5분 데이터는 더 짧은 기간만 유지
                        if timeframe in ['1m', '5m']:
                            days = min(days_to_keep, 30)  # 최대 30일
                            cutoff = int((datetime.now() - timedelta(days=days)).timestamp())
                        else:
                            cutoff = cutoff_timestamp

                        cursor = await db.execute(f"""
                            DELETE FROM {table_name} WHERE timestamp < ?
                        """, (cutoff,))

                        deleted_count = cursor.rowcount
                        if deleted_count > 0:
                            logger.info(f"Cleaned up {deleted_count} old records from {db_file.stem}:{timeframe}")

                    await db.execute("VACUUM")
                    await db.commit()

            except Exception as e:
                logger.error(f"Error cleaning up {db_file}: {e}")

    async def get_cache_stats(self) -> Dict[str, Any]:
        """캐시 통계 조회"""
        total_size = 0
        file_counts = {}

        for db_file in self.cache_dir.glob("*.db"):
            size_mb = db_file.stat().st_size / (1024 * 1024)
            total_size += size_mb
            file_counts[db_file.stem] = {
                'size_mb': round(size_mb, 2),
                'last_modified': datetime.fromtimestamp(db_file.stat().st_mtime).isoformat()
            }

        return {
            'total_size_mb': round(total_size, 2),
            'memory_cache_size': len(self.memory_cache),
            'files': file_counts,
            **self.cache_stats
        }

    async def optimize_databases(self):
        """데이터베이스 최적화"""
        for db_file in self.cache_dir.glob("*.db"):
            try:
                async with aiosqlite.connect(str(db_file)) as db:
                    await db.execute("ANALYZE")
                    await db.execute("VACUUM")
                    await db.commit()

                logger.info(f"Optimized database: {db_file.stem}")

            except Exception as e:
                logger.error(f"Error optimizing {db_file}: {e}")

    async def _log_access(self, exchange: str, symbol: str, timeframe: str,
                         operation: str, duration_ms: int):
        """액세스 로그 기록"""
        try:
            db_path = self.cache_dir / "stats.db"
            async with aiosqlite.connect(str(db_path)) as db:
                await db.execute("""
                    INSERT INTO access_log (exchange, symbol, timeframe, operation, duration_ms)
                    VALUES (?, ?, ?, ?, ?)
                """, (exchange, symbol, timeframe, operation, duration_ms))
                await db.commit()
        except Exception as e:
            logger.error(f"Error logging access: {e}")

    def _generate_data_hash(self, candle: MarketDataPoint) -> str:
        """데이터 해시 생성 (중복 확인용)"""
        data_str = f"{candle.symbol}{candle.timestamp}{candle.open}{candle.high}{candle.low}{candle.close}{candle.volume}"
        return hashlib.md5(data_str.encode()).hexdigest()[:16]

    async def close(self):
        """캐시 시스템 종료"""
        self.executor.shutdown(wait=True)
        logger.info("Data cache system closed")


class HistoricalDataDownloader:
    """21GB급 역사 데이터 다운로더 (Gekko 방식)"""

    def __init__(self, cache_manager: DataCacheManager):
        self.cache_manager = cache_manager
        self.download_stats = {'total_downloaded': 0, 'total_size_mb': 0}

    async def download_all_crypto_history(self, exchanges: List[str] = None):
        """전체 암호화폐 역사 데이터 다운로드"""
        if exchanges is None:
            exchanges = ['binance', 'coinbase', 'kraken', 'bitfinex']

        logger.info("Starting massive historical data download...")

        for exchange in exchanges:
            await self._download_exchange_data(exchange)

        logger.info(f"Download completed. Total: {self.download_stats['total_downloaded']} records, "
                   f"Size: {self.download_stats['total_size_mb']:.2f} MB")

    async def _download_exchange_data(self, exchange: str):
        """거래소별 데이터 다운로드"""
        # 주요 암호화폐 목록
        major_pairs = [
            'BTC/USDT', 'ETH/USDT', 'ADA/USDT', 'DOT/USDT', 'SOL/USDT',
            'MATIC/USDT', 'LINK/USDT', 'UNI/USDT', 'AVAX/USDT', 'ATOM/USDT'
        ]

        timeframes = ['1d', '4h', '1h', '15m', '5m']  # 1m는 너무 크므로 제외

        for symbol in major_pairs:
            for timeframe in timeframes:
                try:
                    # 실제 API 호출 대신 시뮬레이션 (실제 구현시 CCXT 사용)
                    fake_data = self._generate_fake_historical_data(symbol, timeframe)
                    await self.cache_manager.store_candles(exchange, symbol, timeframe, fake_data)

                    self.download_stats['total_downloaded'] += len(fake_data)
                    logger.info(f"Downloaded {len(fake_data)} records for {exchange}:{symbol}:{timeframe}")

                except Exception as e:
                    logger.error(f"Error downloading {exchange}:{symbol}:{timeframe}: {e}")

    def _generate_fake_historical_data(self, symbol: str, timeframe: str) -> List[MarketDataPoint]:
        """실제 API 대신 가짜 역사 데이터 생성 (테스트용)"""
        # 실제 구현에서는 CCXT 등을 사용해 진짜 데이터 다운로드
        fake_data = []

        # 시간프레임별 데이터 포인트 수 계산
        timeframe_minutes = {
            '1m': 1, '5m': 5, '15m': 15, '1h': 60, '4h': 240, '1d': 1440
        }

        # 1년치 데이터
        total_points = (365 * 24 * 60) // timeframe_minutes.get(timeframe, 1440)
        total_points = min(total_points, 50000)  # 최대 5만개 제한

        base_price = 50000 if 'BTC' in symbol else 3000
        current_time = datetime.now() - timedelta(days=365)

        for i in range(total_points):
            # 간단한 랜덤 워크
            price_change = np.random.normal(0, base_price * 0.01)
            base_price = max(base_price + price_change, base_price * 0.5)

            high = base_price * (1 + abs(np.random.normal(0, 0.002)))
            low = base_price * (1 - abs(np.random.normal(0, 0.002)))
            volume = abs(np.random.normal(1000000, 500000))

            fake_data.append(MarketDataPoint(
                timestamp=current_time,
                open=base_price,
                high=high,
                low=low,
                close=base_price,
                volume=volume,
                symbol=symbol,
                exchange="test",
                timeframe=timeframe
            ))

            # 다음 시간포인트로
            current_time += timedelta(minutes=timeframe_minutes.get(timeframe, 1440))

        return fake_data


# 전역 캐시 매니저 인스턴스
_global_cache_manager = None


async def get_cache_manager() -> DataCacheManager:
    """전역 캐시 매니저 반환"""
    global _global_cache_manager
    if _global_cache_manager is None:
        config = DataCacheConfig()
        _global_cache_manager = DataCacheManager(config)
        await _global_cache_manager.initialize()
    return _global_cache_manager