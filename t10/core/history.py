"""
История исправлений: кольцевой буфер + SQLite персистентность.
Хранит последние 500 исправлений для возможности отката (undo).
"""
import sqlite3
import threading
from collections import deque
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "stats.sqlite3"
TABLE_NAME = "corrections"
MAX_HISTORY = 500


@dataclass
class CorrectionRecord:
    timestamp: float
    original: str
    corrected: str
    window_title: str
    process_name: str
    undone: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_row(cls, row: tuple) -> "CorrectionRecord":
        return cls(
            timestamp=row[0],
            original=row[1],
            corrected=row[2],
            window_title=row[3],
            process_name=row[4],
            undone=bool(row[5])
        )


class CorrectionHistory:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = Path(db_path) if not isinstance(db_path, Path) else db_path
        self.buffer: deque[CorrectionRecord] = deque(maxlen=MAX_HISTORY)
        self.lock = threading.Lock()
        self._init_db()
        self._load_from_db()

    def _init_db(self):
        """Инициализация таблицы в SQLite."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                original TEXT,
                corrected TEXT,
                window_title TEXT,
                process_name TEXT,
                undone INTEGER DEFAULT 0
            )
        """)
        conn.commit()
        conn.close()

    def _load_from_db(self):
        """Загрузка последних MAX_HISTORY записей при старте."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT timestamp, original, corrected, window_title, process_name, undone
                FROM {TABLE_NAME}
                ORDER BY id DESC
                LIMIT ?
            """, (MAX_HISTORY,))
            rows = cursor.fetchall()
            conn.close()
            
            # Загружаем в обратном порядке (от старых к новым)
            for row in reversed(rows):
                self.buffer.append(CorrectionRecord.from_row(row))
        except Exception as e:
            print(f"[WARNING] Не удалось загрузить историю из БД: {e}")

    def add(self, original: str, corrected: str, window_title: str, process_name: str):
        """Добавление новой записи об исправлении."""
        record = CorrectionRecord(
            timestamp=datetime.now().timestamp(),
            original=original,
            corrected=corrected,
            window_title=window_title,
            process_name=process_name,
            undone=False
        )
        
        with self.lock:
            self.buffer.append(record)
            self._save_to_db(record)

    def _save_to_db(self, record: CorrectionRecord):
        """Сохранение одной записи в БД."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            cursor.execute(f"""
                INSERT INTO {TABLE_NAME} (timestamp, original, corrected, window_title, process_name, undone)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (record.timestamp, record.original, record.corrected, 
                  record.window_title, record.process_name, int(record.undone)))
            
            # Удаляем старые записи, если их больше MAX_HISTORY
            cursor.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}")
            count = cursor.fetchone()[0]
            if count > MAX_HISTORY:
                # Удаляем самые старые (с минимальным ID)
                cursor.execute(f"""
                    DELETE FROM {TABLE_NAME}
                    WHERE id IN (
                        SELECT id FROM {TABLE_NAME} ORDER BY id ASC LIMIT ?
                    )
                """, (count - MAX_HISTORY,))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[ERROR] Ошибка сохранения в БД: {e}")

    def get_last(self) -> Optional[CorrectionRecord]:
        """Получение последней неотмененной записи."""
        with self.lock:
            for record in reversed(self.buffer):
                if not record.undone:
                    return record
        return None

    def mark_undone(self, record: CorrectionRecord):
        """Пометка записи как отмененной."""
        record.undone = True
        with self.lock:
            try:
                conn = sqlite3.connect(str(self.db_path))
                cursor = conn.cursor()
                # Обновляем по уникальным полям (timestamp + original)
                cursor.execute(f"""
                    UPDATE {TABLE_NAME}
                    SET undone = 1
                    WHERE timestamp = ? AND original = ? AND corrected = ?
                """, (record.timestamp, record.original, record.corrected))
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"[ERROR] Ошибка обновления статуса undo в БД: {e}")

    def get_all(self) -> List[CorrectionRecord]:
        """Получение всех записей (для отладки/статистики)."""
        with self.lock:
            return list(self.buffer)

    def clear(self):
        """Очистка истории."""
        with self.lock:
            self.buffer.clear()
            try:
                conn = sqlite3.connect(str(self.db_path))
                cursor = conn.cursor()
                cursor.execute(f"DELETE FROM {TABLE_NAME}")
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"[ERROR] Ошибка очистки БД: {e}")
