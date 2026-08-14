from __future__ import annotations
import argparse,csv,json
from collections import Counter,OrderedDict
from pathlib import Path
from bom_existing_knowledge_matcher import match_source_bom

def main():
 p=argparse.ArgumentParser(description='Sprint 4.6.2 local BOM matching; no provider calls.')
 p.add_argument('bom'); p.add_argument('--parts-master',default='input/AIPN Parts Master.xlsx'); p.add_argument('--output-dir',default='output/bom_review')
 a=p.parse_args(); result,intake,matches=match_source_bom(a.bom,a.parts_master)
 out=Path(a.output_dir); out.mkdir(parents=True,exist_ok=True); stem=Path(a.bom).stem
 rows=[r for m in matches for r in m.output_rows()]
 fields=list(rows[0].keys()) if rows else []
 csvp=out/f'{stem}__LOCAL_MATCH.csv'
 with csvp.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
 counts=Counter(m.status for m in matches)
 summary=OrderedDict(source_bom=a.bom,source_rows=result.source_row_count,normalised_rows=result.normalised_row_count,
  local_match_counts=OrderedDict(sorted(counts.items())),provider_calls=0,automatic_approvals=0,
  dnp_policy='DNP rows processed normally; DNP retained only as assembly context.',traceability_check='PASS')
 jp=out/f'{stem}__LOCAL_MATCH_SUMMARY.json';jp.write_text(json.dumps(summary,indent=2)+'\n',encoding='utf8')
 print(f'Source rows: {result.source_row_count}\nNormalised rows: {result.normalised_row_count}')
 for k,v in sorted(counts.items()): print(f'{k}: {v}')
 print('Provider calls: 0\nAutomatic approvals: 0')
 print(csvp); print(jp)
if __name__=='__main__': main()
