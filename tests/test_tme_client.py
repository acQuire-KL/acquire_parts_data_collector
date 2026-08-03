import unittest

from config import TmeSettings
from providers.base_provider import ProviderConfigurationError
from providers.tme.client import TmeClient


class FakeResponse:
    def __init__(self, payload, status_code=200, text=""):
        self.payload = payload
        self.status_code = status_code
        self.text = text

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self, auth_payload=None, search_payload=None):
        self.auth_payload = auth_payload or {"access_token": "access-value"}
        self.search_payload = search_payload or {"products": []}
        self.calls = []

    def post(self, url, **kwargs):
        self.calls.append(("POST", url, kwargs))
        return FakeResponse(self.auth_payload)

    def get(self, url, **kwargs):
        self.calls.append(("GET", url, kwargs))
        return FakeResponse(self.search_payload)


class TmeClientTests(unittest.TestCase):
    def test_requires_both_credentials(self):
        client = TmeClient(TmeSettings(token="", application_secret=""), session=FakeSession())
        with self.assertRaises(ProviderConfigurationError):
            client.search_products("ABC")

    def test_search_authenticates_then_uses_bearer_token_and_official_parameters(self):
        session = FakeSession(search_payload={"products": []})
        settings = TmeSettings(
            token="token-value",
            application_secret="secret-value",
            base_url="https://example.test",
            auth_path="/auth/token",
            search_path="/products/search",
            country="IE",
            language="en",
        )
        payload = TmeClient(settings, session=session).search_products(" MCP1711T-25I/OT ")

        self.assertEqual({"products": []}, payload)
        method, url, kwargs = session.calls[0]
        self.assertEqual("POST", method)
        self.assertEqual("https://example.test/auth/token", url)
        self.assertEqual("client_credentials", kwargs["data"]["grant_type"])
        self.assertEqual("token-value", kwargs["auth"].username)
        self.assertEqual("secret-value", kwargs["auth"].password)

        method, url, kwargs = session.calls[1]
        self.assertEqual("GET", method)
        self.assertEqual("https://example.test/products/search", url)
        self.assertEqual(
            [("country", "IE"), ("scope[]", "products"), ("phrase", "MCP1711T-25I/OT")],
            kwargs["params"],
        )
        self.assertEqual("Bearer access-value", kwargs["headers"]["Authorization"])
        self.assertEqual("application/json", kwargs["headers"]["Accept"])
        self.assertEqual("en", kwargs["headers"]["Accept-Language"])

    def test_anonymous_context_header_is_optional(self):
        session = FakeSession()
        settings = TmeSettings(token="token", application_secret="secret")
        TmeClient(settings, session=session).search_products("ABC", anonymous=True)
        self.assertEqual("anonymous", session.calls[1][2]["headers"]["request-context"])

    def test_product_data_uses_symbol_country_and_currency(self):
        session = FakeSession(search_payload={"status": "OK"})
        settings = TmeSettings(
            token="token", application_secret="secret",
            base_url="https://example.test", data_path="/products/data",
            country="IE", currency="EUR",
        )
        payload = TmeClient(settings, session=session).get_product_data(" PART-1 ")
        self.assertEqual({"status": "OK"}, payload)
        method, url, kwargs = session.calls[1]
        self.assertEqual("GET", method)
        self.assertEqual("https://example.test/products/data", url)
        self.assertEqual(
            [
                ("country", "IE"),
                ("currency", "EUR"),
                ("symbols[]", "PART-1"),
                ("scope[]", "prices"),
                ("scope[]", "stock"),
            ],
            kwargs["params"],
        )

    def test_product_data_accepts_repeated_custom_scopes(self):
        session = FakeSession(search_payload={"status": "OK"})
        settings = TmeSettings(
            token="token", application_secret="secret",
            base_url="https://example.test", data_path="/products/data",
            country="IE", currency="EUR",
        )
        TmeClient(settings, session=session).get_product_data(
            "PART-1", scopes=("prices", "stock", "delivery")
        )
        params = session.calls[1][2]["params"]
        self.assertEqual(
            [("scope[]", "prices"), ("scope[]", "stock"), ("scope[]", "delivery")],
            [item for item in params if item[0] == "scope[]"],
        )

    def test_product_data_rejects_empty_scope_collection(self):
        session = FakeSession(search_payload={"status": "OK"})
        settings = TmeSettings(token="token", application_secret="secret")
        with self.assertRaises(ValueError):
            TmeClient(settings, session=session).get_product_data("PART-1", scopes=[])

    def test_product_parameters_uses_symbol_and_country(self):
        session = FakeSession(search_payload={"status": "OK"})
        settings = TmeSettings(
            token="token", application_secret="secret",
            base_url="https://example.test", parameters_path="/products/parameters",
            country="IE",
        )
        payload = TmeClient(settings, session=session).get_product_parameters(" PART-1 ")
        self.assertEqual({"status": "OK"}, payload)
        method, url, kwargs = session.calls[1]
        self.assertEqual("GET", method)
        self.assertEqual("https://example.test/products/parameters", url)
        self.assertEqual(
            [("country", "IE"), ("symbols[]", "PART-1")],
            kwargs["params"],
        )


if __name__ == "__main__":
    unittest.main()
