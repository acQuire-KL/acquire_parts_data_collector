from provider_profiles.normalization import (
    normalise_mounting,
    normalise_package,
    normalise_url,
    number,
    range_values,
)


def test_common_normalisation_helpers():
    assert normalise_package("SOT23-5") == "SOT-23-5"
    assert normalise_mounting("surface mount") == "SMD"
    assert normalise_url("//example.test/image.jpg") == "https://example.test/image.jpg"
    assert number("3000pcs.") == 3000
    assert range_values("-40...85°C") == (-40.0, 85.0)
    assert range_values("1.4...6V") == (1.4, 6.0)
