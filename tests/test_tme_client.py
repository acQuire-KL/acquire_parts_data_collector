import unittest

from config import TmeSettings
from providers.base_provider import ProviderConfigurationError
from providers.tme.client import TmeClient


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return FakeResponse(self.payload)


class TmeClientTests(unittest.TestCase):
    def test_requires_both_credentials(self):
        client = TmeClient(TmeSettings(token="", application_secret=""), session=FakeSession({}))
        with self.assertRaises(ProviderConfigurationError):
            client.search_products("ABC")

    def test_search_uses_basic_credentials_and_locale(self):
        session = FakeSession({"products": []})
        settings = TmeSettings(
            token="token-value",
            application_secret="secret-value",
            base_url="https://example.test",
            search_path="/v2/products/search",
            country="IE",
            language="en",
        )
        payload = TmeClient(settings, session=session).search_products(" MCP1711T-25I/OT ")

        self.assertEqual({"products": []}, payload)
        url, kwargs = session.calls[0]
        self.assertEqual("https://example.test/v2/products/search", url)
        self.assertEqual({"query": "MCP1711T-25I/OT", "country": "IE"}, kwargs["params"])
        self.assertEqual("application/json", kwargs["headers"]["Accept"])
        self.assertEqual("en", kwargs["headers"]["Accept-Language"])
        self.assertEqual("token-value", kwargs["auth"].username)
        self.assertEqual("secret-value", kwargs["auth"].password)

    def test_anonymous_context_header_is_optional(self):
        session = FakeSession({})
        settings = TmeSettings(token="token", application_secret="secret")
        TmeClient(settings, session=session).search_products("ABC", anonymous=True)
        self.assertEqual("anonymous", session.calls[0][1]["headers"]["request-context"])


if __name__ == "__main__":
    unittest.main()
