"""Configuration management"""

import os
import yaml
from typing import Dict, Any
from pathlib import Path


def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file

    Args:
        config_path: Path to config file

    Returns:
        Dict: Configuration dictionary
    """
    # Default configuration
    default_config = {
        'database': {
            'url': 'sqlite:///event_monitoring.db'
        },
        'scheduler': {
            'time': '20:00',  # 8 PM
            'run_on_start': False
        },
        'job_monitoring': {
            'scrape_known_firms': True,
            'scrape_event_firms': True
        },
        'email': {
            'enabled': False,
            'smtp_server': '',
            'smtp_port': 587,
            'sender_email': '',
            'sender_password': '',
            'recipient_email': ''
        },
        'event_sources': [],  # Additional event sources beyond defaults
        'logging': {
            'level': 'INFO',
            'file': 'event_monitoring.log'
        }
    }

    # Load from file if exists
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            file_config = yaml.safe_load(f) or {}
            # Merge with defaults
            default_config.update(file_config)

    # Override with environment variables
    if os.getenv('DATABASE_URL'):
        default_config['database']['url'] = os.getenv('DATABASE_URL')

    if os.getenv('SCHEDULE_TIME'):
        default_config['scheduler']['time'] = os.getenv('SCHEDULE_TIME')

    if os.getenv('SMTP_SERVER'):
        default_config['email']['enabled'] = True
        default_config['email']['smtp_server'] = os.getenv('SMTP_SERVER')

    if os.getenv('SMTP_PORT'):
        default_config['email']['smtp_port'] = int(os.getenv('SMTP_PORT'))

    if os.getenv('EMAIL_SENDER'):
        default_config['email']['sender_email'] = os.getenv('EMAIL_SENDER')

    if os.getenv('EMAIL_PASSWORD'):
        default_config['email']['sender_password'] = os.getenv('EMAIL_PASSWORD')

    if os.getenv('EMAIL_RECIPIENT'):
        default_config['email']['recipient_email'] = os.getenv('EMAIL_RECIPIENT')

    return default_config


def create_example_config(output_path: str = "config.yaml.example"):
    """Create an example configuration file

    Args:
        output_path: Path to write example config
    """
    example_config = {
        'database': {
            'url': 'sqlite:///event_monitoring.db'
        },
        'scheduler': {
            'time': '20:00',
            'run_on_start': False
        },
        'job_monitoring': {
            'scrape_known_firms': True,
            'scrape_event_firms': True
        },
        'email': {
            'enabled': False,
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'sender_email': 'your-email@gmail.com',
            'sender_password': 'your-app-password',
            'recipient_email': 'recipient@example.com'
        },
        'event_sources': [
            {
                'name': 'My University Events',
                'url': 'https://example.edu/events',
                'rss': None
            }
        ],
        'logging': {
            'level': 'INFO',
            'file': 'event_monitoring.log'
        }
    }

    with open(output_path, 'w') as f:
        yaml.dump(example_config, f, default_flow_style=False, sort_keys=False)


def setup_logging(config: Dict[str, Any]):
    """Setup logging based on configuration

    Args:
        config: Configuration dictionary
    """
    import logging
    from logging.handlers import RotatingFileHandler

    log_config = config.get('logging', {})
    log_level = getattr(logging, log_config.get('level', 'INFO'))
    log_file = log_config.get('file', 'event_monitoring.log')

    # Create formatters
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10 MB
        backupCount=5
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
