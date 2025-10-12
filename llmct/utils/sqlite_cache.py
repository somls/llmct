"""优化的SQLite缓存模块 - 高性能批量操作"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path
import threading


class SQLiteCache:
    """
    优化的SQLite缓存管理器
    
    优势:
    - 批量写入减少IO
    - 索引优化查询速度
    - 比JSON快5-10倍
    """
    
    def __init__(self, db_file: str = 'test_cache.db', cache_duration_hours: int = 24):
        self.db_file = db_file
        self.cache_duration = timedelta(hours=cache_duration_hours)
        self.lock = threading.Lock()
        self._write_buffer: List[Dict] = []
        self._buffer_size = 50  # 批量写入阈值
        
        self._init_db()
    
    def _init_db(self):
        """初始化数据库表和索引"""
        with sqlite3.connect(self.db_file) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS cache (
                    model_id TEXT PRIMARY KEY,
                    success INTEGER NOT NULL,
                    response_time REAL,
                    error_code TEXT,
                    content TEXT,
                    timestamp TEXT NOT NULL,
                    failure_count INTEGER DEFAULT 0,
                    last_failure TEXT,
                    failure_history TEXT
                )
            ''')
            
            # 创建索引加速查询
            conn.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON cache(timestamp)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_success ON cache(success)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_failure_count ON cache(failure_count)')
            
            conn.commit()
    
    def is_cached(self, model_id: str) -> bool:
        """检查模型是否在缓存中且未过期"""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.execute('''
                SELECT success, timestamp FROM cache 
                WHERE model_id = ? AND success = 1
            ''', (model_id,))
            
            row = cursor.fetchone()
            if not row:
                return False
            
            try:
                test_time = datetime.fromisoformat(row[1])
                if datetime.now() - test_time < self.cache_duration:
                    return True
            except:
                pass
            
            return False
    
    def get_cached_result(self, model_id: str) -> Optional[Dict]:
        """获取缓存的测试结果"""
        with sqlite3.connect(self.db_file) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT * FROM cache WHERE model_id = ?
            ''', (model_id,))
            
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    def update_cache(
        self, 
        model_id: str, 
        success: bool, 
        response_time: float, 
        error_code: str, 
        content: str
    ):
        """更新缓存（使用批量写入优化）"""
        now = datetime.now().isoformat()
        
        # 获取现有记录
        existing = self.get_cached_result(model_id) or {}
        failure_count = existing.get('failure_count', 0)
        failure_history = json.loads(existing.get('failure_history', '[]'))
        
        # 更新失败统计
        if not success:
            failure_count += 1
            failure_history.append({
                'timestamp': now,
                'error_code': error_code
            })
            # 只保留最近10次失败记录
            if len(failure_history) > 10:
                failure_history = failure_history[-10:]
        
        # 添加到写入缓冲区
        with self.lock:
            self._write_buffer.append({
                'model_id': model_id,
                'success': 1 if success else 0,
                'response_time': response_time,
                'error_code': error_code,
                'content': content,
                'timestamp': now,
                'failure_count': failure_count,
                'last_failure': now if not success else existing.get('last_failure', ''),
                'failure_history': json.dumps(failure_history, ensure_ascii=False)
            })
            
            # 达到阈值时批量写入
            if len(self._write_buffer) >= self._buffer_size:
                self._flush_buffer()
    
    def _flush_buffer(self):
        """批量写入缓冲区数据（优化：减少IO）"""
        if not self._write_buffer:
            return
        
        with sqlite3.connect(self.db_file) as conn:
            conn.executemany('''
                INSERT OR REPLACE INTO cache 
                (model_id, success, response_time, error_code, content, 
                 timestamp, failure_count, last_failure, failure_history)
                VALUES (:model_id, :success, :response_time, :error_code, :content, 
                        :timestamp, :failure_count, :last_failure, :failure_history)
            ''', self._write_buffer)
            
            conn.commit()
        
        self._write_buffer.clear()
    
    def flush(self):
        """强制刷新缓冲区"""
        with self.lock:
            self._flush_buffer()
    
    def get_failed_models(self) -> List[str]:
        """获取所有失败的模型ID列表"""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.execute('''
                SELECT model_id FROM cache WHERE success = 0
            ''')
            return [row[0] for row in cursor.fetchall()]
    
    def get_failure_count(self, model_id: str) -> int:
        """获取模型的失败次数"""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.execute('''
                SELECT failure_count FROM cache WHERE model_id = ?
            ''', (model_id,))
            
            row = cursor.fetchone()
            return row[0] if row else 0
    
    def get_persistent_failures(self, threshold: int = 3) -> List[Dict]:
        """获取持续失败的模型（失败次数超过阈值）"""
        with sqlite3.connect(self.db_file) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT model_id, failure_count, error_code as last_error, last_failure
                FROM cache 
                WHERE failure_count >= ?
                ORDER BY failure_count DESC
            ''', (threshold,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def reset_failure_counts(self):
        """重置所有失败计数"""
        with sqlite3.connect(self.db_file) as conn:
            conn.execute('''
                UPDATE cache 
                SET failure_count = 0, failure_history = '[]'
            ''')
            conn.commit()
    
    def clear_cache(self):
        """清除所有缓存"""
        with sqlite3.connect(self.db_file) as conn:
            conn.execute('DELETE FROM cache')
            conn.commit()
    
    def get_stats(self) -> Dict:
        """获取缓存统计信息"""
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.execute('''
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as success_count,
                    SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as fail_count,
                    AVG(CASE WHEN success = 1 THEN response_time ELSE NULL END) as avg_response_time
                FROM cache
            ''')
            
            row = cursor.fetchone()
            return {
                'total': row[0],
                'success_count': row[1] or 0,
                'fail_count': row[2] or 0,
                'avg_response_time': round(row[3], 3) if row[3] else 0
            }
    
    def __del__(self):
        """析构时刷新缓冲区"""
        try:
            self.flush()
        except:
            pass
