import unittest

from provider_profiles.pdc_part_profile import PDCPartProfile
from providers.digikey.normalizer import build_digikey_pdc_part_profile
from providers.mouser.normalizer import build_mouser_pdc_part_profile
from providers.tme.normalizer import build_tme_pdc_part_profile


class ProviderProfileConsistencyTests(unittest.TestCase):
    def test_all_three_normalizers_return_the_same_pdc_profile_type_and_sections(self):
        profiles = [
            build_digikey_pdc_part_profile({}),
            build_mouser_pdc_part_profile({}),
            build_tme_pdc_part_profile({}, {}, {}),
        ]
        expected_sections = set(PDCPartProfile().to_dict())
        for profile in profiles:
            self.assertIsInstance(profile, PDCPartProfile)
            self.assertEqual(set(profile.to_dict()), expected_sections)
            self.assertEqual(profile.schema_version, "0.2")


if __name__ == "__main__":
    unittest.main()
