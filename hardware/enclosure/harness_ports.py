"""Fixed narrow harness endpoints from selected source pads and assembly targets."""
import json,math
from pathlib import Path
import electrical_imu,electrical_boost,electrical_latch,electrical_peripherals,electrical_blackpill
import blackpill_mount,blackpill_sense,blackpill_drains,branch_fuses,battery_access,battery_leads,fibonacci_board
HERE=Path(__file__).resolve().parent

def terminals(p=None,design=None):
    if p is None:p=json.loads((HERE.parents[1]/'designs/stacked/parameters.json').read_text())
    design=json.loads((HERE/'electrical-design.json').read_text()) if design is None else design
    parts=design['parts'];result={}
    entries={e['name']:e for e in p['electronics']}
    def place(xy,datum,entry,z):
        x,y=[v-d for v,d in zip(xy,datum)];a=math.radians(entry.get('rotation_deg',0));c,s=math.cos(a),math.sin(a)
        dx,dy=entry.get('mount_datum',entry.get('centre'));return [dx+x*c-y*s,dy+x*s+y*c,z]
    def put(name,point,axis,kind='solder',strip=2.5,owner=None,diameter=1.1,barrel=0):
        # Joint starts at the device surface and extends outward. Its lower end
        # is the insulated-wire endpoint. Dimensions are fabrication targets.
        result[name]={'terminal_mm':point,'axis':axis,'kind':kind,'strip_mm':strip,
                      'joint_diameter_target_mm':diameter,'owner':owner,'barrel_mm':barrel,'joint_length_mm':.8 if barrel else strip,
                      'wire_end_mm':[x+(.8 if barrel else strip)*d for x,d in zip(point,axis)] if kind=='solder' else point}
    for module,name,datum,fn,owner in [
        ('IMU','IMU',[16.51,10.16],lambda:electrical_imu.terminals(parts['IMU']),'IMUPCB'),
        ('GPS','GPS',[25.4,11.43],lambda:electrical_peripherals.terminals('GPS',parts['GPS']),'GPSPCB'),
        ('BLACKPILL','BlackPill',blackpill_mount.DATUM,lambda:electrical_blackpill.terminals(parts['BLACKPILL']),'BlackPillPCB'),
        ('RADIO','Radio',[12.7,14.605],lambda:electrical_peripherals.terminals('RADIO',parts['RADIO']),'RadioPCB'),
        ('SPARKLE','SparkleMotion',[25.4,16.51],lambda:electrical_peripherals.terminals('SPARKLE',parts['SPARKLE']),'SparklePCB')]:
        e=entries[name];z=e['pcb_bottom_z_mm']
        for key,row in fn().items():
            if key=='ANT' or module=='SPARKLE' and key in ['AUX_GND','DATA1','DATA2','DATA3','LED_RAIL']:continue
            pad=row['pad'] if module=='SPARKLE' else key
            thickness=1.57 if module in ['GPS','SPARKLE'] else 1.6
            point=place(row['board_xy_mm'],datum,e,z+thickness)
            put(module+'.'+pad,point,[0,0,1],owner=owner,barrel=thickness)
        if module=='SPARKLE':
            # Factory JP1 side entries, local +X. Source pins are2.54mm pitch.
            for key in ['DATA1','DATA2','DATA3','LED_RAIL']:
                row=fn()[key];xy=row['board_xy_mm'];point=place([48.87,xy[1]],datum,e,z+3.945)
                put(module+'.'+row['pad'],point,[1,0,0],kind='clamp',strip=3.2,owner='SparkleComponents')
    # PowerBoost side-entry clamps: one untinned stranded lead per position.
    e=entries['Boost5V'];z=e['pcb_bottom_z_mm']
    for key,row in electrical_boost.terminals(parts['BOOST']).items():
        xy=row['board_xy_mm']
        if key=='TRIP':put('BOOST.'+row['pad'],place(xy,[14.605,11.43],e,z+1.6),[0,0,1],owner='BoostPCB',strip=2.5)
        else:
            side=-1 if key in ('BAT','INPUT_GND') else 1
            point=place([xy[0]+side*3.4,xy[1]],[14.605,11.43],e,z+5.8)
            put('BOOST.'+row['pad'],point,[side,0,0],kind='clamp',strip=5,owner='BoostTerminal'+row['pad'].split('.')[0])
    e=entries['PowerLatch'];z=parts['LATCH']['mount']['pcb_bottom_z_mm']
    for key,row in electrical_latch.terminals(parts['LATCH']).items():
        xy=row['board_xy_mm']
        if key in ['VIN','VOUT','GND']:
            side=1 if key=='VOUT' else -1
            point=place([xy[0]+side*3.1,xy[1]],[7.62,8.89],e,z-4.25)
            put('LATCH.'+key,point,[side,0,0],kind='clamp',strip=4.5,owner='LatchTerminal'+('VOUT' if side==1 else 'VIN'))
        else:put('LATCH.'+key,place(xy,[7.62,8.89],e,z),[0,0,-1],owner='LatchModule',barrel=1.016)
    # Switch terminal numbering is the rear terminal view in the C&K drawing:
    # left column6/5/4 and right3/2/1, top to bottom. No optical-view mirroring.
    for pin in range(1,7):
        x=p['control_switch_x']+(2.415 if pin<=3 else -2.415)
        y=p['control_switch_y']+((pin-1)%3-1)*4.7
        put('S1.'+str(pin),[x,y,14.83],[0,0,1],strip=3.5,owner='PowerDisconnect',diameter=3.5)
    # The selected Z termination is a3.94mm-long solder lug. Lay the
    #3.5mm stripped end along its outside face; do not assume a hole size
    #or solder a bare end floating above its tip. All dimensions are nominal
    #source geometry or explicit fabrication targets, requiring inspection.
    from harness_stock import group
    for pin in range(1,6):
        row=result['S1.'+str(pin)];side=1 if pin<=3 else -1
        tinned={'main':1.3,'branches':.8,'signals':.52}[group('S1.'+str(pin))]
        x,y,tip=row['terminal_mm'];point=[x+side*(.76/2+tinned/2),y,tip]
        row.update(kind='lug-lap',wire_end_mm=point,joint_lap_target_mm=3.5,
                   tinned_conductor_diameter_target_mm=tinned,
                   bare_tip_mm=[point[0],point[1],tip-3.5],
                   joint_owner='SwitchLugBoot'+str(pin),physical_acceptance='unmeasured')
    for logical,key,owner in [('START','start','StartSwitch'),('MODE','mode','ModeSwitch'),('ACTION','action','ActionSwitch')]:
        x,y=p['control_'+key+'_x'],p['control_'+key+'_y']
        for pin,dx,dy in [('1',3.25,2.25),('3',3.25,-2.25)]:
            side=1 if dy>0 else -1
            put(logical+'.'+pin,[x+dx,y+dy+side*.4,5.9],[0,side,0],owner=owner,strip=2.5,diameter=1.4)
    for key,point in branch_fuses.ports('narrow').items():
        # Fuses lie along their source carrier X or Y stations.
        side=-1 if key.endswith('.1') else 1;axis=[side,0,0] if key.startswith(('F_FIB.','F_RING1.','F_RING2.')) else [0,side,0]
        put(key,point,axis,kind='assembled-exit',strip=branch_fuses.geometry('narrow')['solder_overlap_target_mm'],owner='BranchFuse'+key.split('.')[0])
    e=entries['BlackPill'];datum=blackpill_mount.DATUM;z=e['pcb_bottom_z_mm']
    for key,point in blackpill_drains.source_ports().items():
        side=-1 if key.endswith('.1') else 1
        a=math.radians(e['rotation_deg']);axis=[side*math.cos(a),side*math.sin(a),0]
        put(key,place(point[:2],datum,e,z+point[2]),axis,kind='assembled-exit',strip=3.5,owner='BlackPillDrain'+key.split('.')[0])
    for key,point in blackpill_sense.source_ports().items():
        side=-1 if key.endswith('.1') and not key.startswith('C_SENSE.') else 1
        a=math.radians(e['rotation_deg']);axis=[side*math.cos(a),side*math.sin(a),0]
        name=key.split('.')[0]
        owner='BlackPillSense'+('Capacitor' if name=='C_SENSE' else 'Top' if name.endswith('TOP') else 'Bottom')
        put(key,place(point[:2],datum,e,z+point[2]),axis,kind='assembled-exit',strip=3.5,owner=owner)
    e=entries['BulkCapacitor']
    import capacitor_mount
    cap=capacitor_mount.mounting('narrow')
    for pin,x in [('P',-2.5),('N',2.5)]:put('C_OUT.'+pin,place([x,cap['formed_lead_turn_y_mm']],[0,0],e,cap['formed_lead_exit_z_mm']),[0,0,1],kind='assembled-exit',strip=3.5,owner='BulkCapacitor')
    for key,row in fibonacci_board.terminals(parts['FIBONACCI']).items():put('FIBONACCI.'+key,[*row['board_xy_mm'],p['circle_back_z']],[0,0,-1],owner='FibonacciPCB')
    spec=battery_access.definition();data=battery_leads.layout(spec,'narrow');cx,cy=data['cell_centre_xy_mm'];fz=spec['cradle']['cell_axis_z_mm']+data['final_offset_z_mm'];fy=cy+data['final_offset_y_mm'];fx=cx+spec['contact_leads']['main_fuse_centre_x_from_cell_mm']
    for pin,x in [('1',fx+10),('2',fx-10)]:put('F1.'+pin,[x,fy,fz],[1 if pin=='1' else -1,0,0],kind='assembled-exit',strip=3.5,owner='BatteryMainFuse')
    put('CONTACT_N.tail',[cx-(data['bend_x_mm']-data['return_length_mm']),fy,fz],[1,0,0],kind='continuous-datum',strip=0,owner='BatteryLeadN')
    put('CONTACT_P.tail',result['F1.1']['terminal_mm'],[-1,0,0],kind='existing-contact-lead',strip=0,owner='BatteryLeadP')
    # Three pads on each selected4mm FPC are assembly targets at the input
    # seam. The actual stock pad fit remains a physical inspection item.
    rad=(p['inner_count']*1000/p['strip_density']+p['ring_seam_gap'])/math.tau
    rz=p['circle_back_z']+p['circle_pcb_thickness']+p['led_height']+p['led_baffle_gap']+p['baffle_thickness']+p['stencil_mirror_gap']+p['rear_black_acrylic_thickness']+p['mirror_gap']/2
    for ring,zc,side in [('RING1',rz,1),('RING2',19,-1),('RING3',29,-1)]:
        for pin,dz in [('5V',1.2),('DIN',0),('GND',-1.2)]:
            pad_y=math.sqrt((rad+side*.15)**2-(1.6-side*.55)**2)
            put(ring+'.'+pin,[1.6,pad_y,zc+dz],[0,side,0],strip=2.5,owner= {'RING1':'InnerStrip','RING2':'Side0Strip','RING3':'Side1Strip'}[ring])
    import ring_harness,harness_stock
    for pin,row in result.items():
        if row.get('barrel_mm'):
            row['tinned_conductor_diameter_target_mm']=.8 if harness_stock.group(pin)=='branches' else .52
            row['far_face_projection_mm']=row['strip_mm']-row['barrel_mm']-row['joint_length_mm']
    result['S1.6']['kind']='insulated-unused'
    return ring_harness.augment_ports(result,design['wiring']['stock_limits'])

if __name__=='__main__':
    d=terminals();print(json.dumps(d,indent=2))
