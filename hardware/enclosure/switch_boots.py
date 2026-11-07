"""Insulating fabrication gauges around all six fixed C&K7201 lugs.

Selected RNF-100-1/8 sleeve is formed around the lug and the external bare-wire lap. The4.5x3.5mm finished box is a fabrication target, not a filled plastic part or supplier maximum. These are fitted targets;
actual recovery/insulation must be inspected. S1.6 has a closed unused-end cap.
"""
def native_shapes(ports):
    import FreeCAD as App,Part
    shapes={}
    for pin in range(1,7):
        name='S1.'+str(pin);x,y,tip=ports[name]['terminal_mm'];top=15.3 if pin==6 else tip
        outer=Part.makeBox(4.5,3.5,top-10.89,App.Vector(x-2.25,y-1.75,10.89))
        lug=Part.makeBox(.76,2.03,3.94,App.Vector(x-.38,y-1.015,10.89))
        shape=outer.cut(lug).removeSplitter()
        if not shape.isValid() or len(shape.Solids)!=1:raise ValueError('Invalid fixed-switch insulation '+name)
        shapes['SwitchLugBoot'+str(pin)]=shape
    return shapes
