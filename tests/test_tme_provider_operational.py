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
