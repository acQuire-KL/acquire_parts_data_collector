import json, time
from pathlib import Path
from urllib.parse import quote
import requests

class DigiKeyClient:
    def __init__(self, settings):
        self.s = settings
        self.session = requests.Session()
        self.token = None
        self.expires = 0
        self.cache = Path('cache'); self.cache.mkdir(exist_ok=True)
        self.raw = Path('raw_responses'); self.raw.mkdir(exist_ok=True)

    def _get_token(self):
        if self.token and time.time() < self.expires - 30:
            return self.token
        r = self.session.post(self.s.base_url + '/v1/oauth2/token', data={'client_id':self.s.client_id,'client_secret':self.s.client_secret,'grant_type':'client_credentials'}, timeout=30)
        r.raise_for_status(); data = r.json()
        self.token = data['access_token']; self.expires = time.time() + int(data.get('expires_in',600))
        return self.token

    def details(self, mpn, force=False):
        safe = ''.join(c if c.isalnum() else '_' for c in mpn)[:120]
        cached = self.cache / f'{safe}.json'
        if cached.exists() and not force:
            return json.loads(cached.read_text(encoding='utf-8'))
        headers = {'Authorization':f'Bearer {self._get_token()}','X-DIGIKEY-Client-Id':self.s.client_id,'X-DIGIKEY-Locale-Site':self.s.site,'X-DIGIKEY-Locale-Language':self.s.language,'X-DIGIKEY-Locale-Currency':self.s.currency,'Accept':'application/json'}
        url = self.s.base_url + '/products/v4/search/' + quote(mpn, safe='') + '/productdetails'
        r = self.session.get(url, headers=headers, timeout=30)
        if not r.ok:
            raise RuntimeError(f'DigiKey {r.status_code}: {r.text[:500]}')
        data = r.json(); text = json.dumps(data, indent=2, ensure_ascii=False)
        cached.write_text(text, encoding='utf-8')
        stamp = time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())
        (self.raw / f'{safe}_{stamp}.json').write_text(text, encoding='utf-8')
        return data
