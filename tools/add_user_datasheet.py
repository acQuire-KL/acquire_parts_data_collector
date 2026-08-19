from __future__ import annotations
import argparse,json
from pathlib import Path
from datasheet_integration import integrate_evidence_files

def main():
    p=argparse.ArgumentParser(description='Attach a user-supplied datasheet/specification to PDC evidence.'); p.add_argument('component_json'); p.add_argument('parts_master_index'); p.add_argument('pdf'); p.add_argument('--manufacturer',required=True); p.add_argument('--mpn',required=True); p.add_argument('--source-name',required=True); p.add_argument('--archive-root',default='datasheets'); p.add_argument('--date',required=True); p.add_argument('--manufacturer-url',default=''); p.add_argument('--confirm-manufacturer-document',action='store_true'); a=p.parse_args()
    r=integrate_evidence_files(component_json_path=a.component_json,parts_master_index_path=a.parts_master_index,manufacturer=a.manufacturer,mpn=a.mpn,user_supplied_file=a.pdf,archive_root=Path(a.archive_root),supplied_source_name=a.source_name,added_date=a.date,manufacturer_document_confirmed=a.confirm_manufacturer_document,manufacturer_source_url=a.manufacturer_url)
    print(json.dumps(r.__dict__,indent=2)); return 0 if r.status=='Integrated' else 1
if __name__=='__main__': raise SystemExit(main())
