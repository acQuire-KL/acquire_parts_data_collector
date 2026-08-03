from provider_profiles.pdc_part_profile import PDCPartProfile


def test_pdc_part_profile_serialises_with_neutral_sections():
    profile = PDCPartProfile().to_dict()

    assert profile["schema_version"] == "0.2"
    assert set(profile) == {
        "schema_version", "identity", "technical", "commercial", "logistics",
        "lifecycle", "regulatory", "media", "provider_metadata", "provenance", "raw_references",
    }
    assert "tme" not in str(profile).lower()
