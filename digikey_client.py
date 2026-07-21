from __future__ import annotations

import json
import time
from pathlib import Path
from urllib.parse import quote

import requests


class DigiKeyClient:
    def __init__(self, settings):
        self.s = settings
        self.session = requests.Session()
        self.token = None
        self.expires = 0
        self.cache = Path('cache')
        self.cache.mkdir(exist_ok=True)
        self.raw = Path('raw_responses')
        self.raw.mkdir(exist_ok=True)

    def _get_token(self):
        if self.token and time.time() < self.expires - 30:
            return self.token
        r = self.session.post(
            self.s.base_url + '/v1/oauth2/token',
            data={
                'client_id': self.s.client_id,
                'client_secret': self.s.client_secret,
                'grant_type': 'client_credentials',
            },
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        self.token = data['access_token']
        self.expires = time.time() + int(data.get('expires_in', 600))
        return self.token

    def _headers(self):
        return {
            'Authorization': f'Bearer {self._get_token()}',
            'X-DIGIKEY-Client-Id': self.s.client_id,
            'X-DIGIKEY-Locale-Site': self.s.site,
            'X-DIGIKEY-Locale-Language': self.s.language,
            'X-DIGIKEY-Locale-Currency': self.s.currency,
            'Accept': 'application/json',
        }

    @staticmethod
    def _safe(value):
        return ''.join(c if c.isalnum() else '_' for c in str(value))[:120]

    def _get_json(self, path, params=None):
        r = self.session.get(
            self.s.base_url + path,
            headers=self._headers(),
            params=params,
            timeout=30,
        )
        if not r.ok:
            raise RuntimeError(f'DigiKey {r.status_code}: {r.text[:1000]}')
        return r.json()

    def manufacturers(self, force=False):
        """Return DigiKey's manufacturer list, cached locally."""
        cached = self.cache / '_manufacturers.json'
        if cached.exists() and not force:
            return json.loads(cached.read_text(encoding='utf-8'))

        data = self._get_json('/products/v4/search/manufacturers')
        text = json.dumps(data, indent=2, ensure_ascii=False)
        cached.write_text(text, encoding='utf-8')
        return data

    def details(self, mpn, manufacturer_id=None, force=False):
        """Retrieve one product, optionally restricted by DigiKey manufacturer ID.

        manufacturerId is the supported DigiKey mechanism for generic MPNs used by
        multiple manufacturers (for example SS14 or CR2032).
        """
        safe_mpn = self._safe(mpn)
        suffix = f'_MFG_{manufacturer_id}' if manufacturer_id is not None else ''
        cached = self.cache / f'{safe_mpn}{suffix}.json'
        if cached.exists() and not force:
            return json.loads(cached.read_text(encoding='utf-8'))

        path = '/products/v4/search/' + quote(mpn, safe='') + '/productdetails'
        params = {'manufacturerId': manufacturer_id} if manufacturer_id is not None else None
        data = self._get_json(path, params=params)

        text = json.dumps(data, indent=2, ensure_ascii=False)
        cached.write_text(text, encoding='utf-8')
        stamp = time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())
        raw_name = f'{safe_mpn}{suffix}_{stamp}.json'
        (self.raw / raw_name).write_text(text, encoding='utf-8')
        return data
