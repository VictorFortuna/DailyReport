import aiosqlite
from datetime import date, datetime
from typing import Optional, List, Dict
from database.models import User, Report, DatabaseModel
from utils.logger import get_logger

logger = get_logger(__name__)

class DatabaseService:
    """Database service for managing users and reports"""

    def __init__(self, db_path: str):
        self.db_path = db_path

    async def initialize(self):
        """Initialize database and create tables"""
        try:
            await DatabaseModel.create_tables(self.db_path)
            logger.info(f"Database initialized at {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    # User operations
    async def create_user(self, telegram_id: int, full_name: str, username: str = None) -> Optional[User]:
        """Create new user"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(
                    """INSERT INTO users (telegram_id, full_name, username)
                       VALUES (?, ?, ?)""",
                    (telegram_id, full_name, username)
                )
                await db.commit()

                # Get created user
                user_row = await db.execute(
                    "SELECT * FROM users WHERE id = ?", (cursor.lastrowid,)
                )
                row = await user_row.fetchone()

                if row:
                    user = User.from_row(row)
                    logger.info(f"Created user: {user.full_name} ({user.telegram_id})")
                    return user
                return None

        except Exception as e:
            logger.error(f"Failed to create user {telegram_id}: {e}")
            return None

    async def get_user(self, telegram_id: int) -> Optional[User]:
        """Get user by telegram_id"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(
                    "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
                )
                row = await cursor.fetchone()

                if row:
                    return User.from_row(row)
                return None

        except Exception as e:
            logger.error(f"Failed to get user {telegram_id}: {e}")
            return None

    async def get_all_users(self, active_only: bool = True) -> List[User]:
        """Get all users"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                query = "SELECT * FROM users"
                params = ()

                if active_only:
                    query += " WHERE is_active = 1"

                query += " ORDER BY full_name"

                cursor = await db.execute(query, params)
                rows = await cursor.fetchall()

                return [User.from_row(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to get all users: {e}")
            return []

    async def update_user(self, telegram_id: int, **kwargs) -> bool:
        """Update user data"""
        try:
            if not kwargs:
                return True

            set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
            values = list(kwargs.values()) + [telegram_id]

            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    f"UPDATE users SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE telegram_id = ?",
                    values
                )
                await db.commit()
                logger.info(f"Updated user {telegram_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to update user {telegram_id}: {e}")
            return False

    # Report operations
    async def create_report(self, user_id: int, report_date: str, calls_count: int,
                          kp_plus: int, kp: int, rejections: int, inadequate: int) -> Optional[Report]:
        """Create new report"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(
                    """INSERT OR REPLACE INTO reports
                       (user_id, report_date, calls_count, kp_plus, kp, rejections, inadequate)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (user_id, report_date, calls_count, kp_plus, kp, rejections, inadequate)
                )
                await db.commit()

                # Get created/updated report
                report_row = await db.execute(
                    "SELECT * FROM reports WHERE user_id = ? AND report_date = ?",
                    (user_id, report_date)
                )
                row = await report_row.fetchone()

                if row:
                    report = Report.from_row(row)
                    logger.info(f"Created/updated report for user {user_id} on {report_date}")
                    return report
                return None

        except Exception as e:
            logger.error(f"Failed to create report for user {user_id}: {e}")
            return None

    async def get_report(self, user_id: int, report_date: str) -> Optional[Report]:
        """Get specific report"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(
                    "SELECT * FROM reports WHERE user_id = ? AND report_date = ?",
                    (user_id, report_date)
                )
                row = await cursor.fetchone()

                if row:
                    return Report.from_row(row)
                return None

        except Exception as e:
            logger.error(f"Failed to get report for user {user_id} on {report_date}: {e}")
            return None

    async def get_user_reports(self, user_id: int, limit: int = 10) -> List[Report]:
        """Get user's recent reports"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(
                    "SELECT * FROM reports WHERE user_id = ? ORDER BY report_date DESC LIMIT ?",
                    (user_id, limit)
                )
                rows = await cursor.fetchall()

                return [Report.from_row(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to get reports for user {user_id}: {e}")
            return []

    async def get_daily_reports(self, report_date: str) -> List[Dict]:
        """Get all reports for specific date with user names"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute("""
                    SELECT r.*, u.full_name, u.telegram_id
                    FROM reports r
                    JOIN users u ON r.user_id = u.id
                    WHERE r.report_date = ?
                    ORDER BY u.full_name
                """, (report_date,))
                rows = await cursor.fetchall()

                reports = []
                for row in rows:
                    report = Report.from_row(row)
                    report_dict = report.to_dict()
                    report_dict['full_name'] = row['full_name']
                    report_dict['telegram_id'] = row['telegram_id']
                    reports.append(report_dict)

                return reports

        except Exception as e:
            logger.error(f"Failed to get daily reports for {report_date}: {e}")
            return []

    async def check_report_exists(self, user_id: int, report_date: str) -> bool:
        """Check if report exists for user on specific date"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "SELECT 1 FROM reports WHERE user_id = ? AND report_date = ?",
                    (user_id, report_date)
                )
                row = await cursor.fetchone()
                return row is not None

        except Exception as e:
            logger.error(f"Failed to check report existence for user {user_id}: {e}")
            return False

    async def get_users_without_report(self, report_date: str) -> List[User]:
        """Get all active users who haven't submitted report for specific date"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute("""
                    SELECT u.* FROM users u
                    WHERE u.is_active = 1
                    AND u.telegram_id NOT IN (
                        SELECT u2.telegram_id FROM users u2
                        JOIN reports r ON u2.id = r.user_id
                        WHERE r.report_date = ?
                    )
                    ORDER BY u.full_name
                """, (report_date,))
                rows = await cursor.fetchall()

                return [User.from_row(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to get users without report for {report_date}: {e}")
            return []