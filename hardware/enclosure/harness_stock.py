"""Selected fixed-loom gauge ownership; shared by pads and cut records."""
MAIN=frozenset({'F1.2','S1.1','S1.2','LATCH.VIN','LATCH.VOUT','BOOST.X2.2','CONTACT_N.tail','BOOST.X2.1'})
POWER22=frozenset({'BOOST.X1.1','BOOST.X1.2','S1.4','S1.5','SPARKLE.X7.PWR','SPARKLE.X7.GND','SPARKLE.JP1.9','SPARKLE.JP3.2','BLACKPILL.3V3','GPS.3V','RADIO.VIN','BLACKPILL.GND','GPS.GND','RADIO.GND','FIBONACCI.5V','FIBONACCI.GND','C_OUT.P','C_OUT.N'})

def group(pin):
    if pin in MAIN:return 'main'
    if pin in POWER22 or pin.startswith(('F_FIB.','F_RING','F_AUX.')) or pin.startswith('RING') and pin.endswith(('.5V','.GND')):return 'branches'
    return 'signals'



# Primary catalog2012-09-07, printedpp41-42: selected tin-plated ETFE stock.
# OD maxima use the source inch column. Masses are NOMINAL metric weights.
# Resistance is MAXIMUM at20C, using exact304.8m per1000ft conversion.
REVIEWED_ROWS=(('main','M22759/16-18',.073,11.4,6.23),
               ('branches','M22759/16-22',.054,5.24,16.2),
               ('signals','M22759/18-26',.034,2.26,41.3))


def validate_limits(limits,directory=None):
    import hashlib,json,math
    from pathlib import Path
    directory=Path(__file__).resolve().parent if directory is None else Path(directory)
    source=directory/'sources/wire-m22759';index=json.loads((source/'index.json').read_text())
    expected_hash='72ee89ff2113eb09389dd37345bb8fb22bef44edfc639ed1f869e7c209b6f996'
    if index.get('retained_primary_pdf_sha256')!=expected_hash or hashlib.sha256((source/'amphenol-m22759.pdf').read_bytes()).hexdigest()!=expected_hash:raise ValueError('Selected wire primary source changed')
    if not limits.get('source_revision') or not limits.get('temperature_basis'):raise ValueError('Retain wire source revision and nominal/maximum conditions')
    for name,stock,diameter,nominal_mass,resistance in REVIEWED_ROWS:
        actual=limits.get(name,{})
        expected={'stock':stock,'maximum_od_mm':diameter*25.4,'nominal_mass_g_m':nominal_mass,
                  'maximum_resistance_ohm_m_at_20c':resistance/304.8,'maximum_resistance_ohm_1000ft_at_20c':resistance}
        if set(actual)!=set(expected):raise ValueError('Selected wire limit fields changed '+name)
        for key,value in expected.items():
            item=actual[key]
            if isinstance(value,str):
                if item!=value:raise ValueError('Selected wire stock changed '+name)
            elif isinstance(item,bool) or not isinstance(item,(int,float)) or not math.isfinite(item) or abs(item-value)>1e-12:raise ValueError('Selected wire source value changed '+name+'/'+key)
    return {'primary_pdf_sha256':expected_hash,'resistance_temperature_c':20,'mass_kind':'nominal; retain separate engineering allowances','physical_acceptance':'unmeasured'}
