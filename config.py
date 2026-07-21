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
