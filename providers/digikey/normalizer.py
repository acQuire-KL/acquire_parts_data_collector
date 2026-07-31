"""Map a DigiKey Product Details Knowledge Base record to PDCPartProfile."""
from __future__ import annotations
from typing import Any
from commercial_profile import build_commercial_profile
from provider_profiles.models import *
from provider_profiles.normalization import normalise_mounting, normalise_pack_format, normalise_package, normalise_url, number, range_values

PROVIDER = "DigiKey"

def _unwrap(record):
    record=record or {}; return record.get('provider_response',record), record.get('knowledge_base_metadata',{})

def _product(response):
    p=response.get('Product') if isinstance(response,dict) else None; return p if isinstance(p,dict) else response

def _params(product):
    out={}
    for item in product.get('Parameters') or []:
        if isinstance(item,dict) and item.get('ParameterText'):
            out.setdefault(str(item['ParameterText']),[]).append(str(item.get('ValueText') or ''))
    return out

def _one(params,*names):
    for n in names:
        vals=params.get(n) or []
        if vals and vals[0] not in ('','-'): return vals[0]
    return ''

def _category(product):
    c=product.get('Category') or {}; names=[]
    while isinstance(c,dict) and c:
        if c.get('Name'): names.append(str(c['Name']))
        children=c.get('ChildCategories') or []; c=children[0] if children else {}
    return names

def build_digikey_provider_part_profile(record: dict[str,Any], *, raw_references: dict[str,str]|None=None) -> ProviderPartProfile:
    response, meta=_unwrap(record); product=_product(response); params=_params(product)
    desc=product.get('Description') or {}; manufacturer=product.get('Manufacturer') or {}; status=product.get('ProductStatus') or {}; cls=product.get('Classifications') or {}
    cats=_category(product)
    package_raw=_one(params,'Package / Case'); supplier_package=_one(params,'Supplier Device Package')
    temp_raw=_one(params,'Operating Temperature','Operating Temperature - Junction'); tmin,tmax=range_values(temp_raw)
    input_raw=_one(params,'Voltage - Input (Max)'); input_val=number(input_raw)
    out_v_raw=_one(params,'Voltage - Output (Min/Fixed)','Voltage - Rated'); out_i_raw=_one(params,'Current - Output','Current Rating (Amps)')
    commercial=build_commercial_profile(response,meta)
    offers=commercial.get('offers') or []
    all_breaks=[]
    for offer in offers:
        for b in offer.get('standard_price_breaks') or []:
            x=dict(b); x['provider_part_number']=offer.get('provider_part_number',''); x['pack_format']=offer.get('pack_format',''); all_breaks.append(x)
    formats=list(dict.fromkeys(o.get('pack_format','') for o in offers if o.get('pack_format')))
    moqs=[o.get('minimum_order_quantity') for o in offers if isinstance(o.get('minimum_order_quantity'),(int,float))]
    stdpacks=[o.get('pack_quantity') for o in offers if isinstance(o.get('pack_quantity'),(int,float)) and o.get('pack_quantity')]
    lifecycle_status=str(status.get('Status') or '')
    p=ProviderPartProfile(
      identity=IdentityProfile(manufacturer=str(manufacturer.get('Name') or ''),manufacturer_part_number=str(product.get('ManufacturerProductNumber') or ''),provider_part_number=str((offers[0].get('provider_part_number') if offers else '') or ''),alternative_names=[str(x) for x in product.get('OtherNames') or []],description=str(desc.get('ProductDescription') or ''),detailed_description=str(desc.get('DetailedDescription') or ''),category=cats[0] if cats else '',subcategory=cats[-1] if len(cats)>1 else ''),
      technical=TechnicalProfile(component_type=_one(params,'Type','Technology'),regulator_type=[x for x in [_one(params,'Output Type'),_one(params,'Output Configuration')] if x],manufacturer_series=str((product.get('BaseProductNumber') or {}).get('Name') or (product.get('Series') or {}).get('Name') or ''),package=normalise_package(package_raw or supplier_package),supplier_device_package=normalise_package(supplier_package),mounting_type=normalise_mounting(_one(params,'Mounting Type')),output_voltage_v=float(number(out_v_raw)) if number(out_v_raw) is not None else None,output_current_a=float(number(out_i_raw))/1000 if 'ma' in out_i_raw.lower() and number(out_i_raw) is not None else (float(number(out_i_raw)) if number(out_i_raw) is not None else None),input_voltage_max_v=float(input_val) if input_val is not None else None,operating_temperature_min_c=tmin,operating_temperature_max_c=tmax,tolerance_percent=float(number(_one(params,'Tolerance'))) if number(_one(params,'Tolerance')) is not None else None,channel_count=int(number(_one(params,'Number of Regulators','Number of Channels'))) if number(_one(params,'Number of Regulators','Number of Channels')) is not None else None,additional_attributes={k:v for k,v in params.items() if k not in {'Type','Technology','Output Type','Output Configuration','Package / Case','Supplier Device Package','Mounting Type','Voltage - Output (Min/Fixed)','Voltage - Rated','Current - Output','Current Rating (Amps)','Voltage - Input (Max)','Operating Temperature','Operating Temperature - Junction','Tolerance','Number of Regulators','Number of Channels'}}),
      commercial=CommercialProfile(currency=str(commercial.get('provider_currency') or ''),supplier_moq=min(moqs) if moqs else None,stock_quantity=number(commercial.get('product_quantity_available')),manufacturer_public_quantity=number(commercial.get('manufacturer_public_quantity')),manufacturer_lead_time_weeks=float(number(commercial.get('manufacturer_lead_weeks'))) if number(commercial.get('manufacturer_lead_weeks')) is not None else None,unit_price=float(number(commercial.get('product_unit_price'))) if number(commercial.get('product_unit_price')) is not None else None,price_breaks=all_breaks,offers=offers),
      logistics=LogisticsProfile(sales_unit='pcs',manufacturer_standard_pack_quantity=max(stdpacks) if stdpacks else None,pack_formats=formats),
      lifecycle=LifecycleProfile(status=lifecycle_status,provider_status=[lifecycle_status] if lifecycle_status else [],discontinued=product.get('Discontinued'),end_of_life=product.get('EndOfLife'),normally_stocking=product.get('NormallyStocking'),backorder_allowed=(not product.get('BackOrderNotAllowed')) if product.get('BackOrderNotAllowed') is not None else None,non_cancellable_non_returnable=product.get('Ncnr'),last_buy_date=str(product.get('DateLastBuyChance') or '')),
      regulatory=RegulatoryProfile(rohs_status=str(cls.get('RohsStatus') or ''),reach_status=str(cls.get('ReachStatus') or ''),moisture_sensitivity_level=str(cls.get('MoistureSensitivityLevel') or ''),eccn=str(cls.get('ExportControlClassNumber') or ''),hts_code=str(cls.get('HtsusCode') or '')),
      media=MediaProfile(primary_image_url=normalise_url(product.get('PhotoUrl')),datasheet_url=normalise_url(product.get('DatasheetUrl')),product_url=normalise_url(product.get('ProductUrl')),video_url=normalise_url(product.get('PrimaryVideoUrl'))),
      provider_metadata=ProviderMetadata(provider=PROVIDER,locale=str(meta.get('locale') or ''),currency=str(meta.get('currency') or ''),request_context=str(meta.get('source_mode') or ''),captured_at_utc=str(meta.get('captured_at_utc') or ''),source_endpoints=['Product_Details']),raw_references=raw_references or {})
    def ev(path,raw_name,raw_value,norm,unit=''):
        p.provenance[path]=AttributeEvidence(PROVIDER,'Product_Details',raw_name,raw_value,norm,unit,str(meta.get('captured_at_utc') or ''))
    ev('identity.manufacturer','Product.Manufacturer.Name',manufacturer.get('Name'),p.identity.manufacturer)
    ev('identity.manufacturer_part_number','Product.ManufacturerProductNumber',product.get('ManufacturerProductNumber'),p.identity.manufacturer_part_number)
    ev('technical.package','Package / Case',package_raw,p.technical.package)
    ev('commercial.offers','Product.ProductVariations',product.get('ProductVariations') or [],offers,p.commercial.currency)
    ev('commercial.stock_quantity','Product.QuantityAvailable',product.get('QuantityAvailable'),p.commercial.stock_quantity,'pcs')
    ev('lifecycle.status','Product.ProductStatus.Status',status.get('Status'),p.lifecycle.status)
    ev('regulatory.rohs_status','Product.Classifications.RohsStatus',cls.get('RohsStatus'),p.regulatory.rohs_status)
    return p
