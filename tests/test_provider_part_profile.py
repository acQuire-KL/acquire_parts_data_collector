from provider_profiles.models import ProviderPartProfile


def test_provider_part_profile_serialises_with_neutral_sections():
    profile = ProviderPartProfile().to_dict()

    assert profile["schema_version"] == "0.1"
    assert set(profile) == {
        "schema_version", "identity", "technical", "commercial", "logistics",
        "media", "provider_metadata", "provenance", "raw_references",
    }
    assert "tme" not in str(profile).lower()
