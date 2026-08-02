from providers.tme.normalizer import build_tme_pdc_part_profile


def _record(endpoint, response, currency=""):
    return {
        "knowledge_base_metadata": {
            "provider": "TME",
            "endpoint": endpoint,
            "captured_at_utc": "2026-07-28T20:15:17Z",
            "locale": "en-IE",
            "currency": currency,
            "request_context": "customer-linked",
        },
        "provider_response": response,
    }


def test_tme_three_endpoints_form_one_provider_neutral_profile():
    search = _record("Product_Search", {
        "status": "OK",
        "data": {"products": {"elements": [{
            "symbol": "MCP1711T-25I/OT",
            "manufacturer": {"name": "MICROCHIP TECHNOLOGY"},
            "description": "IC: voltage regulator; LDO,linear,fixed; 2.5V; 0.15A; SOT23-5; SMD",
            "category": {"name": "LDO fixed voltage regulators"},
            "product_status": ["BLOCKED_FOR_ZBL_GENERAL"],
            "minimal_amount": 3,
            "multiples": 1,
            "unit": {"short_name": "pcs"},
            "packing": {"elements": [{"amount": 150}]},
            "weight": {"value": 0.024, "unit": "g"},
            "assets": {"primary_photo": {"prime": "//example.test/photo.jpg"}},
        }]}}},
    )
    data = _record("Product_Data", {
        "status": "OK",
        "data": {"elements": [{
            "symbol": "MCP1711T-25I/OT",
            "stock_quantity": 367,
            "prices": {
                "elements": [
                    {"amount": 3, "price": 0.770, "special": False},
                    {"amount": 10, "price": 0.712, "special": False},
                ],
                "currency": "EUR", "type": "NET",
                "tax": {"type": "VAT", "rate": 0.0},
            },
            "deliveries": None,
        }]},
    }, "EUR")
    parameters = _record("Product_Parameters", {
        "status": "OK",
        "data": {"elements": [{
            "symbol": "MCP1711T-25I/OT",
            "parameters": {"elements": [
                {"name": "Manufacturer", "values": [{"value": "MICROCHIP TECHNOLOGY"}]},
                {"name": "Type of integrated circuit", "values": [{"value": "voltage regulator"}]},
                {"name": "Kind of voltage regulator", "values": [{"value": "fixed"}, {"value": "LDO"}, {"value": "linear"}]},
                {"name": "Output voltage", "values": [{"value": "2.5V"}]},
                {"name": "Output current", "values": [{"value": "0.15A"}]},
                {"name": "Case", "values": [{"value": "SOT23-5"}]},
                {"name": "Mounting", "values": [{"value": "SMD"}]},
                {"name": "Operating temperature", "values": [{"value": "-40...85°C"}]},
                {"name": "Tolerance", "values": [{"value": "±1%"}]},
                {"name": "Input voltage", "values": [{"value": "1.4...6V"}]},
                {"name": "Number of channels", "values": [{"value": "1"}]},
                {"name": "Kind of package", "values": [{"value": "reel"}, {"value": "tape"}]},
                {"name": "Manufacturer standard package", "values": [{"value": "3000pcs."}]},
            ]},
        }]},
    })

    result = build_tme_pdc_part_profile(search, data, parameters).to_dict()

    assert result["provider_metadata"]["provider"] == "TME"
    assert result["identity"]["manufacturer_part_number"] == "MCP1711T-25I/OT"
    assert result["technical"]["package"] == "SOT-23-5"
    assert result["technical"]["output_voltage_v"] == 2.5
    assert result["technical"]["output_current_a"] == 0.15
    assert result["technical"]["input_voltage_min_v"] == 1.4
    assert result["technical"]["input_voltage_max_v"] == 6.0
    assert result["technical"]["operating_temperature_min_c"] == -40.0
    assert result["technical"]["operating_temperature_max_c"] == 85.0
    assert result["commercial"]["supplier_moq"] == 3
    assert result["commercial"]["stock_quantity"] == 367
    assert result["commercial"]["currency"] == "EUR"
    assert result["logistics"]["listed_pack_quantity"] == 150
    assert result["logistics"]["manufacturer_standard_pack_quantity"] == 3000
    assert result["media"]["primary_image_url"].startswith("https://")
    assert result["provenance"]["technical.package"]["raw_value"] == "SOT23-5"
    assert result["provenance"]["technical.package"]["normalised_value"] == "SOT-23-5"
