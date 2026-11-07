"""Render the installed narrow census, without a second mass calculation."""
BEGIN='<!-- BEGIN GENERATED BUILD INVENTORY -->'
END='<!-- END GENERATED BUILD INVENTORY -->'

def section(parts,link_prefix='designs/stacked/exports/'):
    variants=parts['material_variants'];mass=parts['mass_estimate'];dims=parts['dimensions_mm']
    lines=['## Selected narrow build inventory','',
      'The wide design is an inactive archive. This inventory describes the narrow digital prototype.',
      'It includes one protected XTAR21700 6000mAh button-top cell and the complete sewn necklace.',
      'Masses use published component data, net CAD volumes, full installed wire cuts and stated engineering allowances.',
      'Physical fit, strength, heat, electrical recovery and worn mass remain unmeasured.','',
      f"Body: {dims['diameter']:g}mm diameter x {dims['body_depth']:g}mm depth. Fitted assembly pose: {dims['closed_width']:g} x {dims['closed_height']:g} x {dims['closed_depth']:g}mm (width x height x depth). The free neck span has no rigid envelope.",
      f"[Raw census, accounting owners and bounds]({link_prefix}parts.json) · [Service and print package]({link_prefix}prototype-service.zip).",'',
      '| Ring material | Pendant nominal g | Necklace nominal g | Total worn nominal g | Worn low–high g | Margin to2.5lb g | Separate50g target |',
      '| --- | ---: | ---: | ---: | ---: | ---: | --- |']
    for material,record in variants.items():
        m=record['mass_estimate'];low,high=m['total_worn']['range_g']
        lines.append(f"| {material} | {m['complete_pendant']['nominal_g']:.3f} | {m['necklace']['nominal_g']:.3f} | {m['total_worn']['nominal_g']:.3f} | {low:.3f}–{high:.3f} | {m['margin_g']:.3f} | {'met' if m['margin_target_pass'] else 'not met'} |")
    lines.extend(['','The raw limit is1133.980925g. Raw arithmetic determines acceptance; display rounding does not.',
      'Low/high allowances are added independently. They are not confidence intervals or guaranteed physical assembly bounds.',
      'Exclude charger, carried spares, retail stock, trim waste, brims and disposable fit samples.','',
      '| Installed item | Quantity | Nominal g per unit | Low–high g per unit | Basis |',
      '| --- | ---: | ---: | ---: | --- |'])
    for row in variants['glow']['components']:
        low,high=row['mass_range_g_per_unit'];safe=lambda s:str(s).replace('|','/').replace('\n',' ')
        lines.append(f"| {safe(row['label'])} | {row['installed_quantity']:.9g} | {row['mass_g_per_unit']:.6g} | {low:.6g}–{high:.6g} | {safe(row['mass_basis'])} |")
    lines.extend(['','The raw JSON lists each CAD owner exactly once. Alternate ring material changes only its selected material rows.',
      'The complete loom record includes endpoint strips, internal jacket insertions and one continuous negative contact-to-boost lead.',
      'The service guide distinguishes ordinary cell access from rear/radio maintenance. Keep all unexecuted physical tests unmeasured.',''])
    return '\n'.join(lines)


def update(document,parts):
    if document.count(BEGIN)!=1 or document.count(END)!=1:raise ValueError('Design document requires exactly one generated inventory block')
    before,rest=document.split(BEGIN);old,after=rest.split(END)
    return before+BEGIN+'\n'+section(parts)+'\n'+END+after
