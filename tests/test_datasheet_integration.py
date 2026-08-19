from pathlib import Path
import json,tempfile,unittest
from datasheet_evidence import DatasheetEvidence
from datasheet_integration import EVIDENCE_STATUS_MFG_VERIFIED,EVIDENCE_STATUS_NEEDS_VERIFICATION,build_index_datasheet_summary,integrate_acquired_evidence,integrate_evidence_files,integrate_user_supplied_evidence,update_parts_master_index_record

def component(): return {'manufacturer':'Example MFG','mpn':'ABC123','description':'Example component'}
def acquired_evidence(source_type='MFG',verified=True,retrieved='2026-08-15',sha='a'*64):
    return DatasheetEvidence(discovered_via='Example Disti',discovery_source_type='DISTI',discovery_url='https://disti.test/abc',resolved_url='https://mfg.test/abc.pdf',manufacturer_source_url='https://mfg.test/abc.pdf',active_source_url='https://mfg.test/abc.pdf',document_source_type=source_type,document_source_name='Example MFG',local_file='Example_MFG/ABC123/evidence.pdf',retrieved_date=retrieved,sha256=sha,file_size_bytes=123,manufacturer_url_verified=verified,source_resolution_status='Manufacturer Source Verified',notes='test')

class DatasheetIntegrationTests(unittest.TestCase):
    def test_acquired_evidence_creates_full_component_history(self):
        u=integrate_acquired_evidence(component_record=component(),evidence=acquired_evidence(),manufacturer='Example MFG',mpn='ABC123'); b=u['datasheet_evidence']; self.assertEqual(len(b['history']),1); self.assertEqual(b['active']['verification_status'],EVIDENCE_STATUS_MFG_VERIFIED); self.assertEqual(b['active']['evidence_origin'],'PDC_ACQUIRED')
    def test_component_identity_must_match_mfg_and_mpn(self):
        with self.assertRaises(ValueError): integrate_acquired_evidence(component_record=component(),evidence=acquired_evidence(),manufacturer='Wrong',mpn='ABC123')
    def test_user_supplied_confirmed_mfg_document_is_archived(self):
        with tempfile.TemporaryDirectory() as tmp:
            r=Path(tmp); f=r/'original_vendor_spec.pdf'; f.write_bytes(b'%PDF-user-supplied'); u=integrate_user_supplied_evidence(component_record=component(),supplied_file=f,archive_root=r/'datasheets',manufacturer='Example MFG',mpn='ABC123',supplied_source_name='Example MFG',added_date='2026-08-15',manufacturer_document_confirmed=True,manufacturer_source_url='https://mfg.test/abc.pdf'); a=u['datasheet_evidence']['active']; self.assertEqual(a['evidence_origin'],'USER_SUPPLIED'); self.assertTrue(a['manufacturer_document_confirmed']); self.assertFalse(a['manufacturer_url_verified']); self.assertEqual(a['verification_status'],EVIDENCE_STATUS_MFG_VERIFIED); self.assertEqual(a['original_filename'],'original_vendor_spec.pdf'); self.assertTrue(Path(a['local_file']).exists())
    def test_unconfirmed_user_document_needs_verification(self):
        with tempfile.TemporaryDirectory() as tmp:
            r=Path(tmp); f=r/'unknown.pdf'; f.write_bytes(b'%PDF-unknown'); u=integrate_user_supplied_evidence(component_record=component(),supplied_file=f,archive_root=r/'datasheets',manufacturer='Example MFG',mpn='ABC123',supplied_source_name='User',added_date='2026-08-15',manufacturer_document_confirmed=False); self.assertEqual(u['datasheet_evidence']['active']['verification_status'],EVIDENCE_STATUS_NEEDS_VERIFICATION)
    def test_verified_mfg_evidence_replaces_weaker_distributor_evidence(self):
        r=integrate_acquired_evidence(component_record=component(),evidence=acquired_evidence('DISTI',False,'2026-08-14','b'*64),manufacturer='Example MFG',mpn='ABC123'); r=integrate_acquired_evidence(component_record=r,evidence=acquired_evidence('MFG',True,'2026-08-15','c'*64),manufacturer='Example MFG',mpn='ABC123'); self.assertEqual(r['datasheet_evidence']['active']['verification_status'],EVIDENCE_STATUS_MFG_VERIFIED); self.assertEqual(len(r['datasheet_evidence']['history']),2)
    def test_weaker_new_evidence_does_not_replace_verified_mfg(self):
        r=integrate_acquired_evidence(component_record=component(),evidence=acquired_evidence('MFG',True,'2026-08-14','d'*64),manufacturer='Example MFG',mpn='ABC123'); r=integrate_acquired_evidence(component_record=r,evidence=acquired_evidence('DISTI',False,'2026-08-15','e'*64),manufacturer='Example MFG',mpn='ABC123'); self.assertEqual(r['datasheet_evidence']['active']['verification_status'],EVIDENCE_STATUS_MFG_VERIFIED); self.assertEqual(len(r['datasheet_evidence']['history']),2)
    def test_duplicate_evidence_does_not_duplicate_history(self):
        e=acquired_evidence(); r=integrate_acquired_evidence(component_record=component(),evidence=e,manufacturer='Example MFG',mpn='ABC123'); r=integrate_acquired_evidence(component_record=r,evidence=e,manufacturer='Example MFG',mpn='ABC123'); self.assertEqual(len(r['datasheet_evidence']['history']),1)
    def test_index_summary_contains_only_lightweight_active_evidence(self):
        r=integrate_acquired_evidence(component_record=component(),evidence=acquired_evidence(),manufacturer='Example MFG',mpn='ABC123'); s=build_index_datasheet_summary(r); self.assertEqual(s['datasheet_status'],EVIDENCE_STATUS_MFG_VERIFIED); self.assertIn('datasheet_sha256',s); self.assertNotIn('history',s)
    def test_index_record_update_preserves_existing_fields(self):
        r=integrate_acquired_evidence(component_record=component(),evidence=acquired_evidence(),manufacturer='Example MFG',mpn='ABC123'); i={'manufacturer':'Example MFG','mpn':'ABC123','category':'CAP'}; u=update_parts_master_index_record(index_record=i,component_record=r,manufacturer='Example MFG',mpn='ABC123'); self.assertEqual(u['category'],'CAP'); self.assertEqual(u['datasheet_status'],EVIDENCE_STATUS_MFG_VERIFIED)
    def test_file_level_integration_requires_unique_index_match(self):
        with tempfile.TemporaryDirectory() as tmp:
            r=Path(tmp); cp=r/'component.json'; ip=r/'parts_master_index.json'; cp.write_text(json.dumps(component())); ip.write_text(json.dumps([{'manufacturer':'Example MFG','mpn':'ABC123'},{'manufacturer':'Example MFG','mpn':'ABC123'}])); result=integrate_evidence_files(component_json_path=cp,parts_master_index_path=ip,manufacturer='Example MFG',mpn='ABC123',evidence=acquired_evidence()); self.assertEqual(result.status,'Index Match Required'); self.assertFalse(result.component_updated)
    def test_file_level_integration_updates_component_and_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            r=Path(tmp); cp=r/'component.json'; ip=r/'parts_master_index.json'; cp.write_text(json.dumps(component())); ip.write_text(json.dumps({'parts':[{'manufacturer':'Example MFG','mpn':'ABC123','category':'IC'}]})); result=integrate_evidence_files(component_json_path=cp,parts_master_index_path=ip,manufacturer='Example MFG',mpn='ABC123',evidence=acquired_evidence()); self.assertEqual(result.status,'Integrated'); self.assertTrue(result.component_updated); sc=json.loads(cp.read_text()); si=json.loads(ip.read_text()); self.assertIn('datasheet_evidence',sc); self.assertEqual(si['parts'][0]['datasheet_status'],EVIDENCE_STATUS_MFG_VERIFIED)
if __name__=='__main__': unittest.main()
