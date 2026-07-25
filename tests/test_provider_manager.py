import unittest
from unittest.mock import Mock

from providers.base_provider import BaseProvider
from providers.provider_manager import ProviderManager
from providers.provider_result import ProviderStatus


class ExampleProvider(BaseProvider):
    def __init__(self, name="Example", attribute_source="Example API"):
        self._name = name
        self._attribute_source = attribute_source

    @property
    def name(self):
        return self._name

    @property
    def attribute_source(self):
        return self._attribute_source

    @property
    def required_environment_variables(self):
        return ()

    def manufacturers(self, force=False):
        return []

    def details(
        self,
        mpn,
        manufacturer_id=None,
        force=False,
        *,
        input_manufacturer="",
        resolved_manufacturer="",
    ):
        return Mock()


class ProviderManagerTests(unittest.TestCase):
    def test_manager_preserves_registration_order(self):
        first = ExampleProvider("First")
        second = ExampleProvider("Second")

        manager = ProviderManager([first, second])

        self.assertEqual((first, second), manager.providers)
        self.assertEqual(("First", "Second"), manager.names)
        self.assertIs(first, manager.primary)

    def test_provider_can_be_registered_after_construction(self):
        manager = ProviderManager()
        provider = ExampleProvider()

        manager.register(provider)

        self.assertEqual((provider,), manager.providers)

    def test_duplicate_provider_names_are_rejected_case_insensitively(self):
        manager = ProviderManager([ExampleProvider("DigiKey")])

        with self.assertRaisesRegex(ValueError, "already registered"):
            manager.register(ExampleProvider("digikey"))

    def test_primary_requires_at_least_one_registered_provider(self):
        manager = ProviderManager()

        with self.assertRaisesRegex(RuntimeError, "No data providers"):
            _ = manager.primary

    def test_execute_wraps_successful_provider_data(self):
        provider = ExampleProvider()
        expected = {"Manufacturers": []}
        provider.manufacturers = Mock(return_value=expected)
        manager = ProviderManager([provider])

        result = manager.execute(provider, "manufacturers", True)

        self.assertEqual(ProviderStatus.SUCCESS, result.status)
        self.assertTrue(result.succeeded)
        self.assertIs(expected, result.require_data())
        provider.manufacturers.assert_called_once_with(True)

    def test_execute_isolates_provider_errors(self):
        provider = ExampleProvider()
        failure = RuntimeError("API unavailable")
        provider.manufacturers = Mock(side_effect=failure)
        manager = ProviderManager([provider])

        result = manager.execute(provider, "manufacturers")

        self.assertEqual(ProviderStatus.ERROR, result.status)
        self.assertFalse(result.succeeded)
        self.assertEqual("API unavailable", result.message)
        with self.assertRaisesRegex(RuntimeError, "API unavailable"):
            result.require_data()

    def test_execute_rejects_unregistered_provider(self):
        manager = ProviderManager([ExampleProvider("Registered")])

        with self.assertRaisesRegex(ValueError, "not registered"):
            manager.execute(ExampleProvider("Other"), "manufacturers")

    def test_execute_rejects_unknown_operation(self):
        provider = ExampleProvider()
        manager = ProviderManager([provider])

        with self.assertRaisesRegex(AttributeError, "no operation"):
            manager.execute(provider, "unknown")


if __name__ == "__main__":
    unittest.main()
