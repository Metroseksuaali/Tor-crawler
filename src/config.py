"""
Configuration management for Tor Crawler
"""

import os
import yaml
from dataclasses import dataclass, field
from typing import Optional, List
from pathlib import Path


@dataclass
class TorConfig:
    """Tor connection settings"""
    proxy_host: str = "127.0.0.1"
    proxy_port: int = 9050
    control_port: int = 9051
    control_password: Optional[str] = None
    use_stem: bool = False  # Whether to use stem library for circuit renewal


@dataclass
class CrawlerConfig:
    """Core crawler settings"""
    start_url: str
    max_depth: int = 3
    max_pages: int = 100
    max_pages_per_domain: int = 50
    request_delay: float = 2.0  # Seconds between requests
    request_timeout: int = 30  # Seconds
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0"
    follow_external_onion: bool = True  # Whether to follow other .onion domains
    allowed_domains: List[str] = field(default_factory=list)  # Empty = all .onion
    max_retries: int = 3
    obey_robots_txt: bool = True


@dataclass
class StorageConfig:
    """Storage settings"""
    storage_type: str = "json"  # "json" or "sqlite"
    output_dir: str = "./data"
    json_filename: str = "crawled_pages.json"
    sqlite_filename: str = "crawler.db"
    save_html_content: bool = False  # Whether to save full HTML
    max_content_length: int = 1000  # Maximum characters for stored content


@dataclass
class Config:
    """Main configuration object"""
    tor: TorConfig
    crawler: CrawlerConfig
    storage: StorageConfig
    log_level: str = "INFO"

    @classmethod
    def from_yaml(cls, yaml_path: str) -> "Config":
        """Load configuration from YAML file"""
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        # Override with environment variables (ENV priority)
        tor_config = TorConfig(
            proxy_host=os.getenv("TOR_PROXY_HOST", data.get("tor", {}).get("proxy_host", "127.0.0.1")),
            proxy_port=int(os.getenv("TOR_PROXY_PORT", data.get("tor", {}).get("proxy_port", 9050))),
            control_port=int(os.getenv("TOR_CONTROL_PORT", data.get("tor", {}).get("control_port", 9051))),
            control_password=os.getenv("TOR_CONTROL_PASSWORD", data.get("tor", {}).get("control_password")),
            use_stem=data.get("tor", {}).get("use_stem", False)
        )

        crawler_data = data.get("crawler", {})
        crawler_config = CrawlerConfig(
            start_url=os.getenv("START_URL", crawler_data.get("start_url", "")),
            max_depth=int(os.getenv("MAX_DEPTH", crawler_data.get("max_depth", 3))),
            max_pages=int(os.getenv("MAX_PAGES", crawler_data.get("max_pages", 100))),
            max_pages_per_domain=int(crawler_data.get("max_pages_per_domain", 50)),
            request_delay=float(crawler_data.get("request_delay", 2.0)),
            request_timeout=int(crawler_data.get("request_timeout", 30)),
            user_agent=crawler_data.get("user_agent", "Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0"),
            follow_external_onion=crawler_data.get("follow_external_onion", True),
            allowed_domains=crawler_data.get("allowed_domains", []),
            max_retries=int(crawler_data.get("max_retries", 3)),
            obey_robots_txt=crawler_data.get("obey_robots_txt", True)
        )

        storage_data = data.get("storage", {})
        storage_config = StorageConfig(
            storage_type=storage_data.get("storage_type", "json"),
            output_dir=storage_data.get("output_dir", "./data"),
            json_filename=storage_data.get("json_filename", "crawled_pages.json"),
            sqlite_filename=storage_data.get("sqlite_filename", "crawler.db"),
            save_html_content=storage_data.get("save_html_content", False),
            max_content_length=int(storage_data.get("max_content_length", 1000))
        )

        return cls(
            tor=tor_config,
            crawler=crawler_config,
            storage=storage_config,
            log_level=os.getenv("LOG_LEVEL", data.get("log_level", "INFO"))
        )

    def validate(self) -> bool:
        """Validate configuration"""
        errors = []

        if not self.crawler.start_url:
            errors.append("start_url cannot be empty")

        if not self.crawler.start_url.endswith(".onion") and ".onion" not in self.crawler.start_url:
            errors.append("start_url must be a .onion address")

        if self.crawler.max_depth < 1:
            errors.append("max_depth must be at least 1")

        if self.crawler.max_pages < 1:
            errors.append("max_pages must be at least 1")

        if self.crawler.request_delay < 0:
            errors.append("request_delay cannot be negative")

        if self.storage.storage_type not in ["json", "sqlite"]:
            errors.append("storage_type must be 'json' or 'sqlite'")

        if errors:
            raise ValueError(f"Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors))

        return True
