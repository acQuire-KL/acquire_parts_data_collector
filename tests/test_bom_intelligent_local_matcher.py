import json
import tempfile
import unittest
from pathlib import Path

from bom_intelligent_local_matcher import (
    PartsMasterIndex, parse_bom_requirements, _package_key, _parse_capacitance,
    _parse_resistance, _parse_voltage, _parse_tolerance, _parse_dielectric,
)


def part(mpn, *, family="CAP", nominal=1e-5, package="0603", voltage="10V", dielectric="X5R", technology="ceramic", tolerance="±20%"):
    attrs = {"Package": {"Value": package, "Verification": "Provider Verified"}}
    if family == "CAP": attrs["Capacitance"] = {"Value": "10uF", "Verification": "Provider Verified"}
    if voltage is not None: attrs["Voltage_Rated"] = {"Value": voltage, "Verification": "Provider Verified"}
    if dielectric is not None: attrs["Dielectric"] = {"Value": dielectric, "Verification": "Provider Verified"}
    if technology is not None: attrs["Technology"] = {"Value": technology, "Verification": "Single Provider"}
    if tolerance is not None: attrs["Tolerance"] = {"Value": tolerance, "Verification": "Provider Verified"}
    return {"AIPN": None, "Manufacturer": "Test", "MPN": mpn, "Family": family, "Description": "", "Value_Nominal": nominal, "Footprint": package, "Technical_Attributes": attrs}


class TestParsing(unittest.TestCase):
    def test_common_values(self):
        self.assertAlmostEqual(_parse_capacitance("10uF"), 10e-6)
        self.assertEqual(_parse_resistance("4K7"), 4700)
        self.assertEqual(_parse_resistance("15.4k"), 15400)
        self.assertEqual(_parse_voltage("10uF 10V X5R"), 10)
        self.assertEqual(_parse_tolerance("10uF 10V X5R ±20%"), 20)
        self.assertEqual(_parse_dielectric("10uF 10V X5R"), "X5R")
    def test_kicad_package(self):
        self.assertEqual(_package_key("Capacitor_SMD:C_0603_1608Metric"), "0603")


class TestQualification(unittest.TestCase):
    def _index(self, parts):
        td = tempfile.TemporaryDirectory(); self.addCleanup(td.cleanup)
        p = Path(td.name) / "index.json"
        p.write_text(json.dumps({"parts": parts}), encoding="utf-8")
        return PartsMasterIndex(p)

    def test_explicit_voltage_rejects_underrated_candidate(self):
        idx = self._index([part("GOOD", voltage="10V"), part("LOW", voltage="6.3V")])
        req = parse_bom_requirements({"Reference":"C1", "Value":"10uF 10V X5R", "Footprint":"C_0603_1608Metric"})
        viable, rejected = idx.assess_descriptive(req)
        self.assertEqual([x.part["MPN"] for x in viable], ["GOOD"])
        self.assertEqual([x.part["MPN"] for x in rejected], ["LOW"])

    def test_explicit_technology_rejects_tantalum(self):
        idx = self._index([part("CER", technology="ceramic"), part("TANT", technology="tantalum")])
        req = parse_bom_requirements({"Reference":"C1", "Value":"10uF 10V X5R CER", "Footprint":"C_0603_1608Metric"})
        viable, rejected = idx.assess_descriptive(req)
        self.assertEqual([x.part["MPN"] for x in viable], ["CER"])
        self.assertEqual([x.part["MPN"] for x in rejected], ["TANT"])

    def test_unspecified_voltage_does_not_reject(self):
        idx = self._index([part("10V", voltage="10V"), part("6V3", voltage="6.3V")])
        req = parse_bom_requirements({"Reference":"C1", "Value":"10uF", "Footprint":"C_0603_1608Metric"})
        viable, rejected = idx.assess_descriptive(req)
        self.assertEqual({x.part["MPN"] for x in viable}, {"10V", "6V3"})
        self.assertFalse(rejected)

if __name__ == "__main__": unittest.main()
