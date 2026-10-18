extends SceneTree

# Renderer-independent check of each real viewer adapter and mapped LED layout.
# Pass an absolute SCENE_JSON path after --. No CAD import or renderer needed.
const Checks = preload("res://pattern_checks.gd")

func _initialize():
	var args=OS.get_cmdline_user_args()
	if args.size()!=1 or not FileAccess.file_exists(args[0]):
		push_error("Pass one absolute scene.json path")
		quit(1)
		return
	var metadata=JSON.parse_string(FileAccess.get_file_as_string(args[0]))
	if not metadata is Dictionary:
		push_error("Invalid scene metadata")
		quit(1)
		return
	var script=load("res://main.gd")
	if script==null or not script.can_instantiate():
		push_error("Viewer script cannot be instantiated")
		quit(1)
		return
	var viewer=script.new()
	viewer.metadata=metadata
	var passed=true
	for style in range(3):
		viewer.pattern=viewer.PATTERNS.size()-3+style
		if not Checks.check(metadata.leds,style,viewer._pattern_colour): passed=false
	# The adapter fixture never enters the scene tree. Release its constructor's
	# unparented camera, lights, and presentation nodes as well as the adapter.
	for property in viewer.get_script().get_script_property_list():
		var value=viewer.get(property.name)
		if value is Node and value.get_parent()==null: value.free()
	viewer.free()
	if passed: print("DARK ADAPTER CHECK COMPLETE")
	quit(0 if passed else 1)
