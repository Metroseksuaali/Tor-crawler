#!/usr/bin/env python3
"""
Tor Crawler - CLI interface
"""

import asyncio
import argparse
import sys
from pathlib import Path

from src.config import Config
from src.crawler import TorCrawler


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Tor Crawler - Secure and ethical .onion sites explorer',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Use config.yaml file
  python main.py --config config.yaml

  # Override parameters from command line
  python main.py --start-url "http://example.onion" --max-pages 50 --max-depth 2

  # Use SQLite storage
  python main.py --config config.yaml --storage sqlite

SECURITY & ETHICS:
  - Use only for research and educational purposes
  - Comply with local laws
  - Respect server load (don't disable rate limiting)
  - Don't attempt to infiltrate or crash services
  - Don't store or share personal data without permission
        '''
    )

    parser.add_argument(
        '--config', '-c',
        type=str,
        default='config.yaml',
        help='Path to configuration file (default: config.yaml)'
    )

    parser.add_argument(
        '--start-url', '-u',
        type=str,
        help='Start URL (.onion)'
    )

    parser.add_argument(
        '--max-depth', '-d',
        type=int,
        help='Maximum depth (overrides config file)'
    )

    parser.add_argument(
        '--max-pages', '-p',
        type=int,
        help='Maximum pages (overrides config file)'
    )

    parser.add_argument(
        '--storage', '-s',
        choices=['json', 'sqlite'],
        help='Storage type (overrides config file)'
    )

    parser.add_argument(
        '--delay',
        type=float,
        help='Delay between requests in seconds (overrides config file)'
    )

    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Log level (default: INFO)'
    )

    return parser.parse_args()


async def main():
    """Main function"""
    args = parse_arguments()

    # Check that config file exists
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"❌ Error: Configuration file not found: {args.config}")
        print(f"Create the file or use --config parameter to point to an existing file.")
        print(f"\nYou can also specify settings from command line:")
        print(f"  python main.py --start-url 'http://example.onion' --max-pages 50")
        sys.exit(1)

    try:
        # Load configuration
        config = Config.from_yaml(str(config_path))

        # Override with command line parameters
        if args.start_url:
            config.crawler.start_url = args.start_url

        if args.max_depth:
            config.crawler.max_depth = args.max_depth

        if args.max_pages:
            config.crawler.max_pages = args.max_pages

        if args.storage:
            config.storage.storage_type = args.storage

        if args.delay:
            config.crawler.request_delay = args.delay

        if args.log_level:
            config.log_level = args.log_level

        # Validate configuration
        config.validate()

    except FileNotFoundError:
        print(f"❌ Error: Configuration file not found: {args.config}")
        sys.exit(1)

    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        sys.exit(1)

    except Exception as e:
        print(f"❌ Unexpected error in configuration: {e}")
        sys.exit(1)

    # Create and run crawler
    crawler = TorCrawler(config)

    try:
        await crawler.initialize()
        await crawler.crawl()

    except ConnectionError as e:
        print(f"\n❌ Connection error: {e}")
        print(f"\nEnsure that Tor is running:")
        print(f"  - Linux/Mac: 'tor' or 'brew services start tor'")
        print(f"  - Windows: Start Tor Browser or install Tor Expert Bundle")
        print(f"  - Docker: 'docker run -d -p 9050:9050 dperson/torproxy'")
        sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n⚠ Crawl interrupted by user")

    except Exception as e:
        print(f"\n❌ Critical error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    # Run async main
    asyncio.run(main())
