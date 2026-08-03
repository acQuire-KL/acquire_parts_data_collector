import unittest
from providers.digikey.normalizer import build_digikey_pdc_part_profile

class DigiKeyNormalizerTests(unittest.TestCase):
 def test_preserves_multiple_offers_and_adds_neutral_fields(self):
  record={'knowledge_base_metadata':{'provider':'DigiKey','currency':'EUR','locale':'IE','captured_at_utc':'2026-01-01T00:00:00Z'},'provider_response':{'Product':{'Description':{'ProductDescription':'REG','DetailedDescription':'Linear regulator'},'Manufacturer':{'Name':'Microchip Technology'},'ManufacturerProductNumber':'ABC','UnitPrice':0.44,'QuantityAvailable':20,'ManufacturerLeadWeeks':'12','ProductStatus':{'Status':'Active'},'Discontinued':False,'EndOfLife':False,'NormallyStocking':True,'BackOrderNotAllowed':False,'Ncnr':False,'Classifications':{'RohsStatus':'ROHS3 Compliant','ExportControlClassNumber':'EAR99'},'ProductVariations':[{'DigiKeyProductNumber':'ABCCT-ND','PackageType':{'Name':'Cut Tape (CT)'},'StandardPricing':[{'BreakQuantity':1,'UnitPrice':0.44,'TotalPrice':0.44}], 'MyPricing':[], 'MinimumOrderQuantity':1,'StandardPackage':1,'QuantityAvailableforPackageType':20,'DigiReelFee':0,'MarketPlace':False,'TariffActive':False,'Supplier':{'Name':'Microchip'}}], 'Parameters':[{'ParameterText':'Package / Case','ValueText':'SOT-23-5'},{'ParameterText':'Mounting Type','ValueText':'Surface Mount'}]}}}
  p=build_digikey_pdc_part_profile(record).to_dict()
  self.assertEqual(p['schema_version'],'0.2'); self.assertEqual(len(p['commercial']['offers']),1); self.assertEqual(len(p['commercial']['price_breaks']),1); self.assertEqual(p['lifecycle']['status'],'Active'); self.assertEqual(p['regulatory']['eccn'],'EAR99'); self.assertEqual(p['technical']['package'],'SOT-23-5')
if __name__=='__main__': unittest.main()
