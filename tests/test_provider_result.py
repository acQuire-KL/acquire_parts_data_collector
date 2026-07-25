import unittest

from providers.provider_result import ProviderResult, ProviderStatus


class ProviderResultTests(unittest.TestCase):
    def test_non_success_without_exception_raises_descriptive_error(self):
        result = ProviderResult(
            provider_name="Mouser",
            status=ProviderStatus.SKIPPED,
            message="API key not configured",
        )

        with self.assertRaisesRegex(RuntimeError, "API key not configured"):
            result.require_data()


if __name__ == "__main__":
    unittest.main()
