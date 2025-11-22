#!/usr/bin/env python3
"""
Campus Event Monitoring System for Quantitative Finance Firms

Main entry point for running the event and job monitoring system.
"""

import argparse
import sys
from src.config import load_config, create_example_config, setup_logging
from src.scheduler.job_runner import run_scheduled_job, run_once
from src.notifications.notifier import Notifier
from src.database.db_manager import DatabaseManager


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Monitor campus events and job postings from quantitative finance firms'
    )

    parser.add_argument(
        '--config',
        default='config.yaml',
        help='Path to configuration file (default: config.yaml)'
    )

    parser.add_argument(
        '--create-config',
        action='store_true',
        help='Create an example configuration file'
    )

    parser.add_argument(
        '--run-once',
        action='store_true',
        help='Run once and exit (instead of scheduling)'
    )

    parser.add_argument(
        '--test-notification',
        action='store_true',
        help='Send a test notification'
    )

    parser.add_argument(
        '--schedule-time',
        default='20:00',
        help='Time to run daily job in HH:MM format (default: 20:00)'
    )

    args = parser.parse_args()

    # Create example config if requested
    if args.create_config:
        create_example_config()
        print("Created config.yaml.example")
        print("Copy it to config.yaml and customize as needed")
        return 0

    # Load configuration
    try:
        config = load_config(args.config)
    except Exception as e:
        print(f"Error loading configuration: {e}")
        return 1

    # Setup logging
    setup_logging(config)

    # Test notification if requested
    if args.test_notification:
        db = DatabaseManager(config.get('database', {}).get('url', 'sqlite:///event_monitoring.db'))
        notifier = Notifier(db, config)
        notifier.send_test_notification()
        print("Test notification sent")
        return 0

    # Run job
    try:
        if args.run_once:
            print("Running monitoring job once...")
            run_once(config)
            print("Job completed")
        else:
            schedule_time = config.get('scheduler', {}).get('time', args.schedule_time)
            print(f"Starting scheduled job (daily at {schedule_time})...")
            print("Press Ctrl+C to stop")
            run_scheduled_job(config, schedule_time)

    except KeyboardInterrupt:
        print("\nShutting down...")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
