from dataclasses import dataclass
import os
from dotenv import load_dotenv

@dataclass(frozen=True)
class Settings:
    client_id: str
    client_secret: str
    site: str = 'IE'
    language: str = 'en'
    currency: str = 'EUR'
    sandbox: bool = False

    @property
    def base_url(self):
        return 'https://' + ('sandbox-api.digikey.com' if self.sandbox else 'api.digikey.com')

    @classmethod
    def from_env(cls):
        load_dotenv()
        cid = os.getenv('DIGIKEY_CLIENT_ID','').strip()
        secret = os.getenv('DIGIKEY_CLIENT_SECRET','').strip()
        if not cid or not secret:
            raise ValueError('Copy .env.example to .env and enter DigiKey credentials.')
        return cls(cid, secret, os.getenv('DIGIKEY_SITE','IE').upper(), os.getenv('DIGIKEY_LANGUAGE','en'), os.getenv('DIGIKEY_CURRENCY','EUR').upper(), os.getenv('DIGIKEY_SANDBOX','false').lower() in {'1','true','yes'})


@dataclass(frozen=True)
class MouserSettings:
    """Configuration required by the Mouser Search API."""

    api_key: str
    base_url: str = "https://api.mouser.com"
    timeout_seconds: float = 30.0

    @classmethod
    def from_env(cls):
        load_dotenv()
        return cls(api_key=os.getenv("MOUSER_API_KEY", "").strip())


@dataclass(frozen=True)
class TmeSettings:
    """Configuration for the TME Product API v2 connectivity check."""

    token: str
    application_secret: str
    base_url: str = "https://api.tme.eu"
    auth_path: str = "/auth/token"
    search_path: str = "/products/search"
    data_path: str = "/products/data"
    parameters_path: str = "/products/parameters"
    country: str = "IE"
    language: str = "en"
    currency: str = "EUR"
    timeout_seconds: float = 30.0

    @classmethod
    def from_env(cls):
        load_dotenv()
        return cls(
            token=os.getenv("TME_TOKEN", "").strip(),
            application_secret=os.getenv("TME_APPLICATION_SECRET", "").strip(),
            base_url=os.getenv("TME_BASE_URL", "https://api.tme.eu").strip().rstrip("/"),
            auth_path=os.getenv("TME_AUTH_PATH", "/auth/token").strip(),
            search_path=os.getenv("TME_SEARCH_PATH", "/products/search").strip(),
            data_path=os.getenv("TME_DATA_PATH", "/products/data").strip(),
            parameters_path=os.getenv("TME_PARAMETERS_PATH", "/products/parameters").strip(),
            country=os.getenv("TME_COUNTRY", "IE").strip().upper(),
            language=os.getenv("TME_LANGUAGE", "en").strip(),
            currency=os.getenv("TME_CURRENCY", "EUR").strip().upper(),
            timeout_seconds=float(os.getenv("TME_TIMEOUT_SECONDS", "30")),
        )
