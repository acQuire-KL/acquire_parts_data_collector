from pathlib import Path
import tempfile, unittest
from datasheet_evidence import *

class DatasheetEvidenceTests(unittest.TestCase):
    def test_tracking_removed(self):
        self.assertEqual(normalise_active_url('https://x.com/a.pdf?utm_source=d&lang=en&ref=1'),'https://x.com/a.pdf?lang=en')
    def test_embedded_url(self):
        u='https://d.example/r?target=https%3A%2F%2Fm.example%2Fa.pdf'
        self.assertEqual(extract_embedded_urls(u),['https://m.example/a.pdf'])
    def test_resolved_mfg_recognised(self):
        r=resolve_datasheet_source(discovery_url='https://d.example/a',resolved_url='https://m.example/a.pdf',manufacturer_domains=['m.example'])
        self.assertEqual(r.document_source_type,DatasheetSourceType.MFG); self.assertFalse(r.manufacturer_url_verified)
    def test_verified_mfg_becomes_active(self):
        r=resolve_datasheet_source(discovery_url='https://d.example/a',resolved_url='https://d.example/cache.pdf',manufacturer_domains=['m.example'],independently_verified_url='https://m.example/a.pdf?utm_source=x')
        self.assertTrue(r.manufacturer_url_verified); self.assertEqual(r.active_source_url,'https://m.example/a.pdf')
    def test_disti_retained_when_mfg_unproven(self):
        r=resolve_datasheet_source(discovery_url='https://d.example/a',resolved_url='https://d.example/cache.pdf',manufacturer_domains=['m.example'])
        self.assertEqual(r.document_source_type,DatasheetSourceType.DISTI); self.assertEqual(r.manufacturer_source_url,'')
    def test_matching_files_classify_copy(self):
        with tempfile.TemporaryDirectory() as t:
            a=Path(t)/'a.pdf'; b=Path(t)/'b.pdf'; a.write_bytes(b'%PDF-same'); b.write_bytes(b'%PDF-same')
            r=resolve_datasheet_source(discovery_url='https://d.example/a',resolved_url='https://d.example/a.pdf',manufacturer_domains=['m.example'],downloaded_distributor_file=a,downloaded_manufacturer_file=b)
            self.assertEqual(r.document_source_type,DatasheetSourceType.DISTI_COPY_OF_MFG)
    def test_filename(self):
        self.assertEqual(make_archive_filename(mpn='ABC/1',source_type='MFG',source_name='Maker',retrieved_date='2026-08-15',document_name='DS1'),'2026-08-15__ABC_1__MFG__Maker__DS1.pdf')
    def test_archive_no_overwrite(self):
        with tempfile.TemporaryDirectory() as t:
            r=Path(t); f=r/'d.pdf'; f.write_bytes(b'one')
            a=archive_datasheet(downloaded_file=f,archive_root=r/'ds',manufacturer_name='Maker',mpn='ABC',source_type='MFG',source_name='Maker',retrieved_date='2026-08-15')
            f.write_bytes(b'two')
            b=archive_datasheet(downloaded_file=f,archive_root=r/'ds',manufacturer_name='Maker',mpn='ABC',source_type='MFG',source_name='Maker',retrieved_date='2026-08-15')
            self.assertNotEqual(a,b); self.assertTrue(a.exists() and b.exists())
    def test_evidence_static_and_active(self):
        with tempfile.TemporaryDirectory() as t:
            r=Path(t); f=r/'d.pdf'; f.write_bytes(b'%PDF-x')
            a=archive_datasheet(downloaded_file=f,archive_root=r/'ds',manufacturer_name='Maker',mpn='ABC',source_type='MFG',source_name='Maker',retrieved_date='2026-08-15')
            sr=resolve_datasheet_source(discovery_url='https://d.example/a',resolved_url='https://m.example/a.pdf',manufacturer_domains=['m.example'],independently_verified_url='https://m.example/a.pdf')
            e=build_evidence_record(archived_file=a,resolution=sr,discovered_via='Disti',discovery_source_type='DISTI',document_source_name='Maker',retrieved_date='2026-08-15',archive_root=r/'ds')
            self.assertTrue(e.local_file.endswith('.pdf')); self.assertEqual(e.active_source_url,'https://m.example/a.pdf'); self.assertEqual(len(e.sha256),64)
    def test_change_detection(self):
        with tempfile.TemporaryDirectory() as t:
            a=Path(t)/'a.pdf'; b=Path(t)/'b.pdf'; a.write_bytes(b'old'); b.write_bytes(b'new')
            x=compare_active_to_static(static_file=a,current_download=b); self.assertTrue(x['changed']); self.assertEqual(x['status'],'Changed')

if __name__=='__main__': unittest.main()
