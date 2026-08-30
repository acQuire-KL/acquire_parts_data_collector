import unittest

from config import TmeSettings
from providers.tme.provider import TmeProvider


class DummyKB:
    pass


class TmeProviderOperationalTests(unittest.TestCase):
    def test_provider_identity_and_required_credentials(self):
        provider = TmeProvider(
            TmeSettings(token="x", application_secret="y"),
            knowledge_base=DummyKB(),
            client=object(),
        )
        self.assertEqual("TME", provider.name)
        self.assertEqual(
            ("TME_TOKEN", "TME_APPLICATION_SECRET"),
            provider.required_environment_variables,
        )

    def test_first_symbol_reads_tme_search_shape(self):
        payload = {"data": {"products": {"elements": [{"symbol": "ABC123"}]}}}
        self.assertEqual("ABC123", TmeProvider._first_symbol(payload))

    def test_first_symbol_falls_back_cleanly(self):
        self.assertEqual("", TmeProvider._first_symbol({}))


if __name__ == "__main__":
    unittest.main()

class _TokenReuseClient:
    def __init__(self):
        self.token_calls = 0
        self.tokens_seen = []

    def access_token(self):
        self.token_calls += 1
        return "TOKEN"

    def search_products(self, mpn, access_token=None):
        self.tokens_seen.append(access_token)
        return {"data": {"products": {"elements": [{"symbol": mpn}]}}}

    def get_product_data(self, symbol, access_token=None):
        self.tokens_seen.append(access_token)
        return {"data": {"elements": [{"symbol": symbol, "stock_quantity": 0, "prices": {"elements": [], "currency": "EUR"}}]}}

    def get_product_parameters(self, symbol, access_token=None):
        self.tokens_seen.append(access_token)
        return {"data": {"elements": [{"symbol": symbol, "parameters": {"elements": []}}]}}


class _KBForTokenReuse:
    def save_raw_provider_response(self, **kwargs):
        from knowledge_base_manager import KnowledgeRecord
        return KnowledgeRecord(kwargs["provider_response"], {"provider": "TME", "captured_at_utc": "2026-01-01T00:00:00Z"}, {}, None)


class TmeTokenReuse472aTests(unittest.TestCase):
    def test_one_token_is_reused_for_tme_detail_endpoints(self):
        client = _TokenReuseClient()
        provider = TmeProvider(TmeSettings(token="x", application_secret="y"), knowledge_base=_KBForTokenReuse(), client=client)
        provider.details("ABC123", input_manufacturer="MFG")
        self.assertEqual(1, client.token_calls)
        self.assertEqual(["TOKEN", "TOKEN", "TOKEN"], client.tokens_seen)
