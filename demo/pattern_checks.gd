extends RefCounted

const Patterns = preload("res://patterns.gd")
const STEPS = 512
const DT = 8.0/STEPS

static func colour(style: int, position: Vector2, fibonacci: bool, seconds: float) -> Color:
	match style:
		0: return Patterns.dark_sectors(position,fibonacci,seconds)
		1: return Patterns.dark_spirals(position,fibonacci,seconds)
		2: return Patterns.dark_diagonals(position,fibonacci,seconds)
	return Color.BLACK

static func difference(a: Color, b: Color) -> float:
	return maxf(absf(a.r-b.r),maxf(absf(a.g-b.g),absf(a.b-b.b)))

static func check(leds: Array, style: int, adapter: Callable) -> bool:
	assert(Patterns.EDGE_WIDTH*Patterns.CYCLE_SECONDS>=0.25)
	var totals={}
	for led in leds:
		var group=int(led.group)
		if not totals.has(group): totals[group]=[0.0,0.0]
	var black_seen={}
	var lit_seen={}
	var previous={}
	for step in range(STEPS):
		var seconds=step*DT
		var black={}
		var lit={}
		for led in leds:
			var group=int(led.group)
			var key=Vector2i(group,int(led.index))
			var p=Vector2(led.position_m[0],led.position_m[1])
			var result: Color=adapter.call(led,seconds)
			assert(difference(result,colour(style,p,group==0,seconds))<0.000001,"Viewer adapter differs from shared calculation")
			assert(is_finite(result.r) and is_finite(result.g) and is_finite(result.b))
			assert(result.r>=0 and result.g>=0 and result.b>=0 and result.r<=1 and result.g<=1 and result.b<=1 and result.a==1)
			if result.v==0:
				black[group]=true
				black_seen[key]=true
			if result.v==1:
				lit[group]=true
				lit_seen[key]=true
			if previous.has(key):
				# |dRGB/dt| <= 6/8 + 1.5/(0.08*8) < 3.10 /s.
				assert(difference(result,previous[key])<=3.10*DT+0.00001,"Temporal discontinuity")
			previous[key]=result
			var base=Patterns.rainbow(p,group==0,seconds)
			totals[group][0]+=result.r+result.g+result.b
			totals[group][1]+=base.r+base.g+base.b
		# Each actual output row must remain partly lit at every sampled time.
		for group in totals:
			assert(black.has(group) and lit.has(group),"Whole output row flashed or lost its dark region")
	assert(black_seen.size()==leds.size() and lit_seen.size()==leds.size(),"Dark edges must pass every LED")
	for led in leds:
		var key=Vector2i(int(led.group),int(led.index))
		var end: Color=adapter.call(led,8.0)
		assert(difference(end,adapter.call(led,0.0))<0.00001,"Mapped LED cycle must close")
		assert(difference(end,previous[key])<=3.10*DT+0.00001,"Mapped LED repeat boundary must stay smooth")
	for group in totals:
		assert(totals[group][0]<0.75*totals[group][1],"Expected a substantial RGB-demand reduction")
		print("DARK RGB PROXY: style=%s group=%d dt=%.6fs period=8s reduction=%.3f%%" % [Patterns.DARK_NAMES[style],group,DT,100*(1-totals[group][0]/totals[group][1])])
	# Full-period join and a small frame on each side of that join, including origin.
	var probes=[Vector2.ZERO,Vector2(0,0.0795),Vector2(0.02385,0.0318)]
	for fibonacci in [true,false]:
		for p in probes:
			assert(difference(colour(style,p,fibonacci,0),colour(style,p,fibonacci,8))<0.00001)
			assert(difference(colour(style,p,fibonacci,8-0.00001),colour(style,p,fibonacci,0.00001))<0.0001)
			for seconds in [0.0,1.75,4.0,7.99]:
				var a=colour(style,Vector2(-0.00000001,0.0795),fibonacci,seconds)
				var b=colour(style,Vector2(0.00000001,0.0795),fibonacci,seconds)
				assert(difference(a,b)<0.00001,"Angular seam")
			var coarse=0.0
			var fine=0.0
			for frame in range(48): coarse+=1.0/24.0
			for frame in range(120): fine+=1.0/60.0
			assert(difference(colour(style,p,fibonacci,coarse),colour(style,p,fibonacci,fine))<0.00001,"Frame-step history changed output")
	# All ring radii use the same unit-radius field, including Cartesian bands.
	for seconds in [0.0,1.75,3.0]:
		assert(difference(colour(style,Vector2(0.04,0.03),false,seconds),colour(style,Vector2(0.08,0.06),false,seconds))<0.00001)
	# Independent scalar reference values for a future Rust/libm port (RGB, linear).
	var expected=[
		[Color(1,0.375,0),Color(0,0,0),Color(0.024719238,0.009269714,0)],
		[Color(0.327641964,0,0.476570129),Color(0.327641964,0,0.476570129),Color(0.6875,0,1)],
		[Color(0,0,0),Color(0.926998294,0,1),Color(0.827793238,0,0.892982483)],
	]
	assert(difference(colour(style,Vector2(0.03975,0),true,1.5),expected[0][style])<0.00001)
	assert(difference(colour(style,Vector2(0,0.0795),false,1.75),expected[1][style])<0.00001)
	assert(difference(colour(style,Vector2(0.02385,0.0318),true,2.25),expected[2][style])<0.00001)
	print("DARK PATTERN PASS: "+Patterns.DARK_NAMES[style])
	return true
