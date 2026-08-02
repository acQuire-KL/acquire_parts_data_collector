from __future__ import annotations
import argparse,json,re
from pathlib import Path
from providers.digikey.normalizer import build_digikey_pdc_part_profile

def safe(v): return re.sub(r'[^A-Za-z0-9._-]+','_',str(v)).strip('_')
def main():
 p=argparse.ArgumentParser(); p.add_argument('mpn',nargs='?',default='MCP1711T-25I/OT'); p.add_argument('--manufacturer',default='Microchip Technology'); p.add_argument('--knowledge-base',default='Knowledge_Base'); p.add_argument('--output',default='output/provider_profiles'); a=p.parse_args()
 path=Path(a.knowledge_base)/'Current'/'DigiKey'/'Product_Details'/f'{safe(a.manufacturer)}__{safe(a.mpn)}.json'
 if not path.exists():
  matches=list((Path(a.knowledge_base)/'Current'/'DigiKey'/'Product_Details').glob(f'*__{safe(a.mpn)}.json')); path=matches[0] if matches else path
 data=json.load(path.open(encoding='utf-8')); profile=build_digikey_pdc_part_profile(data,raw_references={'product_details':str(path)}).to_dict()
 out=Path(a.output); out.mkdir(parents=True,exist_ok=True); op=out/f'DIGIKEY__{safe(profile["identity"]["manufacturer"])}__{safe(a.mpn)}.json'; json.dump(profile,op.open('w',encoding='utf-8'),indent=2,ensure_ascii=False)
 print('DIGIKEY NORMALISED PDC PART PROFILE'); print('Manufacturer :',profile['identity']['manufacturer']); print('MPN          :',profile['identity']['manufacturer_part_number']); print('Offers       :',len(profile['commercial']['offers'])); print('Price breaks :',len(profile['commercial']['price_breaks'])); print('Saved profile:',op); return 0
if __name__=='__main__': raise SystemExit(main())
