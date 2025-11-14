#!/usr/bin/env python3
"""
Tor Crawler - CLI-käyttöliittymä
"""

import asyncio
import argparse
import sys
from pathlib import Path

from src.config import Config
from src.crawler import TorCrawler


def parse_arguments():
    """Parsii komentoriviargumentit"""
    parser = argparse.ArgumentParser(
        description='Tor Crawler - Turvallinen .onion-sivustojen tutkija',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Esimerkkejä:
  # Käytä config.yaml-tiedostoa
  python main.py --config config.yaml

  # Ohita parametrit komentoriviltä
  python main.py --start-url "http://example.onion" --max-pages 50 --max-depth 2

  # Käytä SQLite-tallennusta
  python main.py --config config.yaml --storage sqlite

TURVALLISUUS JA ETIIKKA:
  - Käytä vain tutkimus- ja oppimistarkoituksiin
  - Noudata paikallisia lakeja
  - Kunnioita palvelinten kuormaa (älä poista rate limitingiä)
  - Älä yritä tunkeutua tai kaataa palveluita
  - Älä tallenna henkilötietoja ilman lupaa
        '''
    )

    parser.add_argument(
        '--config', '-c',
        type=str,
        default='config.yaml',
        help='Polku konfiguraatiotiedostoon (oletus: config.yaml)'
    )

    parser.add_argument(
        '--start-url', '-u',
        type=str,
        help='Aloitus-URL (.onion)'
    )

    parser.add_argument(
        '--max-depth', '-d',
        type=int,
        help='Maksimisyvyys (ohittaa config-tiedoston)'
    )

    parser.add_argument(
        '--max-pages', '-p',
        type=int,
        help='Maksimisivumäärä (ohittaa config-tiedoston)'
    )

    parser.add_argument(
        '--storage', '-s',
        choices=['json', 'sqlite'],
        help='Tallennustyyppi (ohittaa config-tiedoston)'
    )

    parser.add_argument(
        '--delay',
        type=float,
        help='Viive pyyntöjen välillä sekunteina (ohittaa config-tiedoston)'
    )

    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Lokitaso (oletus: INFO)'
    )

    return parser.parse_args()


async def main():
    """Pääfunktio"""
    args = parse_arguments()

    # Tarkista että config-tiedosto on olemassa
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"❌ Virhe: Konfiguraatiotiedostoa ei löydy: {args.config}")
        print(f"Luo tiedosto tai käytä --config -parametria osoittamaan olemassa oleva tiedosto.")
        print(f"\nVoit myös määritellä asetukset komentoriviltä:")
        print(f"  python main.py --start-url 'http://example.onion' --max-pages 50")
        sys.exit(1)

    try:
        # Lataa konfiguraatio
        config = Config.from_yaml(str(config_path))

        # Ohita komentoriviparametreilla
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

        # Validoi konfiguraatio
        config.validate()

    except FileNotFoundError:
        print(f"❌ Virhe: Konfiguraatiotiedostoa ei löydy: {args.config}")
        sys.exit(1)

    except ValueError as e:
        print(f"❌ Konfiguraatiovirhe: {e}")
        sys.exit(1)

    except Exception as e:
        print(f"❌ Odottamaton virhe konfiguraatiossa: {e}")
        sys.exit(1)

    # Luo ja aja crawler
    crawler = TorCrawler(config)

    try:
        await crawler.initialize()
        await crawler.crawl()

    except ConnectionError as e:
        print(f"\n❌ Yhteysvirhe: {e}")
        print(f"\nVarmista että Tor on käynnissä:")
        print(f"  - Linux/Mac: 'tor' tai 'brew services start tor'")
        print(f"  - Windows: Käynnistä Tor Browser tai asenna Tor Expert Bundle")
        print(f"  - Docker: 'docker run -d -p 9050:9050 dperson/torproxy'")
        sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n⚠ Crawlaus keskeytetty käyttäjän toimesta")

    except Exception as e:
        print(f"\n❌ Kriittinen virhe: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    # Aja async main
    asyncio.run(main())
