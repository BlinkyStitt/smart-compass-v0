extends RefCounted

const FPS = 24.0
const FRAMES = 384
const DISTANCE = 0.46
const TARGET = Vector3(0,0,0.0367)

# A closed figure eight on the viewing sphere. The pointing-hand side
# stops at +20 degrees; the clear side reaches -50 degrees. The asymmetry
# is smooth at both head-on crossings, including the loop boundary.
static func yaw(frame: float) -> float:
	var side=sin(TAU*frame/FRAMES)
	return 35.0*side-15.0*side*side

static func pitch(frame: float) -> float:
	return 20.0*sin(2.0*TAU*frame/FRAMES)

# These hand meshes are convex. Their projected hulls describe the actual
# silhouette, including the fingertip, without empty bounding-box corners.
static func hand_overlaps(camera: Camera3D, mannequin: Node3D, radius: float, front_z: float) -> bool:
	var face=PackedVector2Array()
	for i in range(128):
		var angle=TAU*i/128.0
		face.append(camera.unproject_position(Vector3(radius*sin(angle),radius*cos(angle),front_z)))
	for surface in mannequin.surfaces:
		if not (str(surface.name).begins_with("Pointing") or str(surface.name).begins_with("CurledFinger")):
			continue
		var world_points=PackedVector3Array()
		var nearest_z=-INF
		for index in range(surface.mesh.get_surface_count()):
			for vertex in surface.mesh.surface_get_arrays(index)[Mesh.ARRAY_VERTEX]:
				var world_point=surface.global_transform*vertex
				world_points.append(world_point)
				nearest_z=maxf(nearest_z,world_point.z)
		# The shoulder and upper arm can project over the pendant from the
		# far side, but sit behind its front face and cannot hide it.
		if nearest_z<=front_z:
			continue
		var points=PackedVector2Array()
		for point in world_points:
			points.append(camera.unproject_position(point))
		if not Geometry2D.intersect_polygons(face,Geometry2D.convex_hull(points)).is_empty():
			return true
	return false
