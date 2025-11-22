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

    parser.add_argument(
        '--search',
        type=str,
        help='Search for content across all types (events, jobs, blogs, reports, videos)'
    )

    parser.add_argument(
        '--storage-stats',
        action='store_true',
        help='Show storage statistics'
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

    # Search content if requested
    if args.search:
        db = DatabaseManager(config.get('database', {}).get('url', 'sqlite:///event_monitoring.db'))
        results = db.search_content(args.search)

        print(f"\nSearch results for '{args.search}':\n")

        for content_type, items in results.items():
            if items:
                print(f"\n{content_type.upper()} ({len(items)} found):")
                print("-" * 80)
                for item in items[:10]:  # Show first 10
                    title = getattr(item, 'title', 'No title')
                    url = getattr(item, 'url', None) or getattr(item, 'job_url', None) or getattr(item, 'event_url', 'No URL')
                    firm = getattr(item, 'firm', None)
                    firm_name = firm.name if firm else 'Unknown'
                    print(f"  • {title}")
                    print(f"    Firm: {firm_name}")
                    print(f"    URL: {url}")
                    print()

        return 0

    # Show storage stats if requested
    if args.storage_stats:
        from src.storage import ContentStorage
        storage = ContentStorage(config.get('storage', {}).get('base_dir', 'content_storage'))
        stats = storage.get_storage_stats()

        print("\nContent Storage Statistics:\n")
        print("-" * 60)

        total_size = 0
        total_files = 0

        for content_type, type_stats in stats.items():
            print(f"\n{content_type.upper().replace('_', ' ')}:")
            print(f"  Files: {type_stats['count']}")
            print(f"  Size: {type_stats['size_mb']} MB")
            total_size += type_stats['size_mb']
            total_files += type_stats['count']

        print(f"\n{'-' * 60}")
        print(f"TOTAL:")
        print(f"  Files: {total_files}")
        print(f"  Size: {total_size:.2f} MB")
        print()

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
