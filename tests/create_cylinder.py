import bpy

# Add a simple cylinder at the center of the scene
bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=2, location=(0, 0, 0))

# Print a success message to the Blender system console
print("Cylinder created successfully via external script!")