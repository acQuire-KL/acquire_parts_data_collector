import tempfile,unittest
from pathlib import Path
from openpyxl import Workbook
from bom_existing_knowledge_matcher import _engineering_value,_package_key,match_source_bom,STATUS_VALUE_UNIQUE

class TestLocalMatcher(unittest.TestCase):
 def test_value_parser(self):
  self.assertAlmostEqual(_engineering_value('100nF','C1'),1e-7)
  self.assertEqual(_engineering_value('4K7','R1'),4700)
 def test_package_parser(self):
  self.assertEqual(_package_key('Capacitor_SMD:C_0201_0603Metric'),'0201')
 def test_unique_value_footprint_is_candidate_not_approval(self):
  with tempfile.TemporaryDirectory() as td:
   td=Path(td); bom=td/'b.csv'; bom.write_text('Reference,MF,MPN,Value,Footprint,Qty,DNP\nC1,,,100nF,Capacitor_SMD:C_0201_0603Metric,1,\n',encoding='utf8')
   pm=td/'p.xlsx'; wb=Workbook();ws=wb.active;ws.title='My Lists Worksheet';ws.append(['AIPN','Family','Value','Case','Description','Manufacturer Name','Manufacturer Part Number','AIPN - OLD']);ws.append(['CAP-00010-00','CAP',1e-7,'0201','Cap','Murata','ABC','']);wb.save(pm)
   _,_,m=match_source_bom(bom,pm)
   self.assertEqual(m[0].status,STATUS_VALUE_UNIQUE); self.assertEqual(len(m[0].candidates),1)

if __name__=='__main__': unittest.main()
