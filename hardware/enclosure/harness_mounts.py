"""PCB-backed fixed splice cradles with two spot ties and isolated foam feet.

The1mm fitted adhesive thickness and all completed splice/tie envelopes are
assembly targets. Adhesion, material compatibility and wearing are unmeasured.
"""
import math
import harness_plan

def native_shapes(plan=None):
    import FreeCAD as App,Part
    plan=harness_plan.definition() if plan is None else plan;products={};pads={};target={};pcb_back=harness_plan.parameters()['circle_back_z']
    def box(x0,x1,y0,y1,z0,z1):return Part.makeBox(x1-x0,y1-y0,z1-z0,App.Vector(x0,y0,z0))
    for name,data in plan['splices'].items():
        x,y,z=data['centre_mm'];r=data.get('body_diameter_target_mm',data['diameter_target_mm'])/2;L=data.get('body_length_target_mm',data['length_target_mm']);full_L=data['length_target_mm'];end_r=data['diameter_target_mm']/2;lo,hi=y-L/2,y+L/2;outer=r+.25+1.35;bottom=z-r-1.35
        floor=box(x-outer,x+outer,lo,hi,bottom,z-r)
        left=box(x-outer,x-r-.25,lo,hi,z-r,(pcb_back-2.35))
        right=box(x+r+.25,x+outer,lo,hi,z-r,(pcb_back-2.35))
        cradle=floor.fuse(left).fuse(right)
        foot_r=end_r if end_r>r else r
        feet=box(x-foot_r-.25-3,x-r-.25,lo,hi,(pcb_back-2.35),(pcb_back-1)).fuse(box(x+r+.25,x+foot_r+.25+3,lo,hi,(pcb_back-2.35),(pcb_back-1)))
        for side in [-1,1]:
            a,b=(x-foot_r-.25-3,x-foot_r-.25) if side<0 else (x+foot_r+.25,x+foot_r+.25+3)
            feet=feet.fuse(box(a,b,y-full_L/2,y+full_L/2,(pcb_back-2.35),(pcb_back-1)))
        adhesive=box(x-foot_r-.25-3,x-foot_r-.25,y-full_L/2,y+full_L/2,(pcb_back-1),pcb_back).fuse(box(x+foot_r+.25,x+foot_r+.25+3,y-full_L/2,y+full_L/2,(pcb_back-1),pcb_back))
        cuts=[]
        for i,ty in enumerate([y-L/4,y+L/4]):
            top=z+r
            loop=box(x-outer-.5,x+outer+.5,ty-.85,ty+.85,bottom-.5,top+.5).cut(box(x-outer,x+outer,ty-1,ty+1,bottom,top))
            # Knot/tails on the rear side, below the printed floor. They cannot
            # enter the LED PCB or the adhesive bonding plane.
            knot=box(x-1,x+3,ty-1.1,ty+1.1,bottom-2.5,bottom-.3)
            products['HarnessSpliceTie'+name+str(i)]=loop.fuse(knot).removeSplitter()
            for side in [-1,1]:
                a,b=(x-foot_r-.25-3.1,x-r-.15) if side<0 else (x+r+.15,x+foot_r+.25+3.1)
                cuts.append(box(a,b,ty-1.05,ty+1.05,min((pcb_back-2.45),top-.1),(pcb_back+.1)))
        cut=Part.makeCompound(cuts);cradle=cradle.fuse(feet).cut(cut).removeSplitter();adhesive=adhesive.cut(cut)
        if not cradle.isValid() or len(cradle.Solids)!=1:raise ValueError('Invalid splice cradle '+name)
        products['HarnessSpliceCarrier'+name]=cradle
        products['HarnessSpliceTape'+name]=adhesive
        target['HarnessSplice'+name]=Part.makeCylinder(r,L,App.Vector(x,lo,z),App.Vector(0,1,0))
        if full_L>L:
            for a,b in [(y-full_L/2,lo),(hi,y+full_L/2)]:target['HarnessSplice'+name]=target['HarnessSplice'+name].fuse(Part.makeCylinder(end_r,b-a,App.Vector(x,a,z),App.Vector(0,1,0))).removeSplitter()
    for name,data in plan['splices'].items():
        angle=data.get('rotation_deg',0);x,y,z=data['centre_mm']
        if angle not in [0,90]:raise ValueError('Select the checked splice orientation')
        if angle:
            for key,shape in {**products,**target}.items():
                if key in {'HarnessSpliceCarrier'+name,'HarnessSpliceTape'+name,'HarnessSplice'+name,*('HarnessSpliceTie'+name+str(i) for i in range(2))}:shape.rotate(App.Vector(x,y,0),App.Vector(0,0,1),angle)
    return {'products':products,'splices':target,'adhesive':'3M VHB5952; fit1.0mm compressed from maker1.1mm nominal stock; no guaranteed bond or thickness claim','physical_acceptance':'unmeasured'}
