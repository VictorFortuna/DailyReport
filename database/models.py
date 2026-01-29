import sqlite3
import aiosqlite
from datetime import datetime
from typing import Optional, Dict, List

class DatabaseModel:
    """Base database model with common functionality"""

    @staticmethod
    async def create_tables(db_path: str):
        """Create all database tables"""
        async with aiosqlite.connect(db_path) as db:
            # Users table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER UNIQUE NOT NULL,
                    full_name TEXT NOT NULL,
                    username TEXT,
                    is_admin BOOLEAN DEFAULT 0,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Reports table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    report_date DATE NOT NULL,
                    calls_count INTEGER NOT NULL,
                    kp_plus INTEGER NOT NULL,
                    kp INTEGER NOT NULL,
                    rejections INTEGER NOT NULL,
                    inadequate INTEGER NOT NULL,
                    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    UNIQUE(user_id, report_date)
                )
            ''')

            # Settings table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Pending registrations table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS pending_registrations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER UNIQUE NOT NULL,
                    full_name TEXT NOT NULL,
                    username TEXT,
                    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected'))
                )
            ''')

            # Blocked users table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS blocked_users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER UNIQUE NOT NULL,
                    full_name TEXT,
                    username TEXT,
                    reason TEXT,
                    blocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    blocked_by INTEGER NOT NULL,
                    FOREIGN KEY (blocked_by) REFERENCES users(id)
                )
            ''')

            await db.commit()

class User:
    """User model"""

    def __init__(self, id: int = None, telegram_id: int = None, full_name: str = None,
                 username: str = None, is_admin: bool = False, is_active: bool = True,
                 created_at: datetime = None, updated_at: datetime = None):
        self.id = id
        self.telegram_id = telegram_id
        self.full_name = full_name
        self.username = username
        self.is_admin = is_admin
        self.is_active = is_active
        self.created_at = created_at
        self.updated_at = updated_at

    def to_dict(self) -> Dict:
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'telegram_id': self.telegram_id,
            'full_name': self.full_name,
            'username': self.username,
            'is_admin': self.is_admin,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> 'User':
        """Create User instance from database row"""
        return cls(
            id=row['id'],
            telegram_id=row['telegram_id'],
            full_name=row['full_name'],
            username=row['username'],
            is_admin=bool(row['is_admin']),
            is_active=bool(row['is_active']),
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None,
        )

class Report:
    """Report model"""

    def __init__(self, id: int = None, user_id: int = None, report_date: str = None,
                 calls_count: int = 0, kp_plus: int = 0, kp: int = 0,
                 rejections: int = 0, inadequate: int = 0, submitted_at: datetime = None):
        self.id = id
        self.user_id = user_id
        self.report_date = report_date
        self.calls_count = calls_count
        self.kp_plus = kp_plus
        self.kp = kp
        self.rejections = rejections
        self.inadequate = inadequate
        self.submitted_at = submitted_at

    def to_dict(self) -> Dict:
        """Convert report to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'report_date': self.report_date,
            'calls_count': self.calls_count,
            'kp_plus': self.kp_plus,
            'kp': self.kp,
            'rejections': self.rejections,
            'inadequate': self.inadequate,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
        }

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> 'Report':
        """Create Report instance from database row"""
        return cls(
            id=row['id'],
            user_id=row['user_id'],
            report_date=row['report_date'],
            calls_count=row['calls_count'],
            kp_plus=row['kp_plus'],
            kp=row['kp'],
            rejections=row['rejections'],
            inadequate=row['inadequate'],
            submitted_at=datetime.fromisoformat(row['submitted_at']) if row['submitted_at'] else None,
        )

class PendingRegistration:
    """Pending registration model"""

    def __init__(self, id: int = None, telegram_id: int = None, full_name: str = None,
                 username: str = None, requested_at: datetime = None, status: str = 'pending'):
        self.id = id
        self.telegram_id = telegram_id
        self.full_name = full_name
        self.username = username
        self.requested_at = requested_at
        self.status = status

    def to_dict(self) -> Dict:
        """Convert pending registration to dictionary"""
        return {
            'id': self.id,
            'telegram_id': self.telegram_id,
            'full_name': self.full_name,
            'username': self.username,
            'requested_at': self.requested_at.isoformat() if self.requested_at else None,
            'status': self.status,
        }

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> 'PendingRegistration':
        """Create PendingRegistration instance from database row"""
        return cls(
            id=row['id'],
            telegram_id=row['telegram_id'],
            full_name=row['full_name'],
            username=row['username'],
            requested_at=datetime.fromisoformat(row['requested_at']) if row['requested_at'] else None,
            status=row['status'],
        )

class BlockedUser:
    """Blocked user model"""

    def __init__(self, id: int = None, telegram_id: int = None, full_name: str = None,
                 username: str = None, reason: str = None, blocked_at: datetime = None,
                 blocked_by: int = None):
        self.id = id
        self.telegram_id = telegram_id
        self.full_name = full_name
        self.username = username
        self.reason = reason
        self.blocked_at = blocked_at
        self.blocked_by = blocked_by

    def to_dict(self) -> Dict:
        """Convert blocked user to dictionary"""
        return {
            'id': self.id,
            'telegram_id': self.telegram_id,
            'full_name': self.full_name,
            'username': self.username,
            'reason': self.reason,
            'blocked_at': self.blocked_at.isoformat() if self.blocked_at else None,
            'blocked_by': self.blocked_by,
        }

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> 'BlockedUser':
        """Create BlockedUser instance from database row"""
        return cls(
            id=row['id'],
            telegram_id=row['telegram_id'],
            full_name=row['full_name'],
            username=row['username'],
            reason=row['reason'],
            blocked_at=datetime.fromisoformat(row['blocked_at']) if row['blocked_at'] else None,
            blocked_by=row['blocked_by'],
        )