"""
Timezone utilities for proper datetime handling
"""
import pytz
from datetime import datetime
from bot.config import Config

def get_moscow_timezone():
    """Get Moscow timezone object"""
    return pytz.timezone(Config.TIMEZONE)

def moscow_now():
    """Get current datetime in Moscow timezone"""
    moscow_tz = get_moscow_timezone()
    return datetime.now(moscow_tz)

def format_moscow_time(dt, format_string='%H:%M'):
    """Convert datetime to Moscow timezone and format it"""
    if dt is None:
        return ""

    # If datetime is naive (no timezone), assume it's UTC
    if dt.tzinfo is None:
        dt = pytz.utc.localize(dt)

    # Convert to Moscow timezone
    moscow_tz = get_moscow_timezone()
    moscow_dt = dt.astimezone(moscow_tz)

    return moscow_dt.strftime(format_string)

def format_moscow_date(dt=None, format_string='%d.%m.%Y'):
    """Get Moscow date string"""
    if dt is None:
        dt = moscow_now()
    return dt.strftime(format_string)