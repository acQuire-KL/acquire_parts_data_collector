import json
import tempfile
import unittest
from pathlib import Path

from config import TmeSettings
from tme_connectivity_check import _save_to_knowledge_base


class TmeKnowledgeBaseCaptureTests(unittest.TestCase):
    def test_raw_tme_response_is_saved_without_invented_profiles(self):
        payload = {
            "products": [
                {
                    "manufacturer": "MICROCHIP TECHNOLOGY",
                    "mpn": "MCP1711T-25I/OT",
                    "symbol": "MCP1711T-25I/OT",
                }
            ]
        }
        settings = TmeSettings(token="token", application_secret="secret")
        with tempfile.TemporaryDirectory() as folder:
            path = _save_to_knowledge_base(
                payload,
                mpn="MCP1711T-25I/OT",
                manufacturer="MICROCHIP TECHNOLOGY",
                settings=settings,
                anonymous=False,
                knowledge_base_root=Path(folder),
            )
            self.assertTrue(path.exists())
            document = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(payload, document["provider_response"])
            self.assertEqual("TME", document["knowledge_base_metadata"]["provider"])
            self.assertEqual("Product_Search", document["knowledge_base_metadata"]["endpoint"])
            self.assertEqual("not_mapped", document["knowledge_base_metadata"]["mapping_status"])
            self.assertNotIn("commercial_profile", document)
            self.assertNotIn("part_profile", document)
            history = list((Path(folder) / "History" / "TME" / "Product_Search").rglob("*.json"))
            self.assertEqual(1, len(history))


if __name__ == "__main__":
    unittest.main()
