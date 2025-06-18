import logging
import os
import sys
from datetime import datetime
from typing import Any

def setup_logging(log_level: str = 'INFO', log_file: str = 'logs/app.log'):
    """
    Setup logging configuration with UTF-8 encoding support
    """
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Force UTF-8 encoding for Windows console
    if sys.platform == 'win32':
        import codecs
        try:
            # Set console code page to UTF-8
            os.system('chcp 65001 > nul')
            # Configure stdout and stderr to use UTF-8
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
            sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
        except Exception:
            pass

    # Configure logging handlers
    handlers = []

    # File handler with UTF-8 encoding
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(
        logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    )
    handlers.append(file_handler)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    )

    # Safe console handler for Windows
    if sys.platform == 'win32':
        class SafeConsoleHandler(logging.StreamHandler):
            def emit(self, record):
                try:
                    msg = self.format(record)
                    self.stream.write(msg + self.terminator)
                    self.flush()
                except UnicodeEncodeError:
                    # Strip non-ASCII characters
                    import re
                    clean_msg = re.sub(r'[^\x00-\x7F]+', '', self.format(record))
                    self.stream.write(clean_msg + self.terminator)
                    self.flush()
                except Exception:
                    self.handleError(record)
        console_handler = SafeConsoleHandler()
        console_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
    handlers.append(console_handler)

    # Apply logging configuration
    logging.basicConfig(
        level=getattr(logging, log_level),
        handlers=handlers
    )

    # Set default formatter
    logging._defaultFormatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def validate_config(config: Any) -> bool:
    """
    Validate required configuration
    """
    required_fields = [
        'TEAMLOGGER_API_URL',
        'TEAMLOGGER_BEARER_TOKEN',
        'SMTP_USERNAME',
        'SMTP_PASSWORD',
        'FROM_EMAIL'
    ]
    missing = []
    for field in required_fields:
        if not getattr(config, field, None):
            missing.append(field)
    if missing:
        logging.error(f"Missing required configuration: {', '.join(missing)}")
        return False
    return True


def format_hours(hours: float) -> str:
    """
    Format hours to a readable string
    """
    h = int(hours)
    m = int((hours - h) * 60)
    return f"{h}h {m}m"


def is_business_day(date: datetime) -> bool:
    """
    Check if a date is a business day (Monday-Friday)
    """
    return date.weekday() < 5


def calculate_hours_per_day(total_hours: float, work_days: int) -> float:
    """
    Calculate average hours per day
    """
    if work_days == 0:
        return 0.0
    return total_hours / work_days


def safe_print(message: str):
    """
    Safely print messages, removing non-ASCII on Windows
    """
    try:
        print(message)
    except UnicodeEncodeError:
        import re
        clean = re.sub(r'[^\x00-\x7F]+', '', message)
        print(clean)


def get_safe_emoji(emoji: str, fallback: str = '') -> str:
    """
    Return emoji on Unix, fallback text on Windows
    """
    if sys.platform == 'win32':
        emoji_map = {
            '🚀': '[START]', '⏰': '[TIME]', '📊': '[STATS]',
            '📅': '[CALENDAR]', '🤖': '[AI]', '🔍': '[SEARCH]',
            '✅': '[OK]', '❌': '[ERROR]', '⚠️': '[WARNING]',
            '🛑': '[STOP]', '👋': '[BYE]', '💪': '[FORCE]',
            '🧪': '[TEST]', '▶️': '[RUN]', '⏭️': '[SKIP]',
            '📋': '[LIST]', '📬': '[MAIL]', '🎯': '[TARGET]',
            '📈': '[GRAPH]', '⏱️': '[TIMER]'
        }
        return emoji_map.get(emoji, fallback)
    return emoji
