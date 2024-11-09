import trimesh
from trimesh import creation

# Create a cube mesh
# cube = creation.box(extents=(3,))

# Visualize the cube
# cube.show()

# mesh = trimesh.load_mesh("Stanford_Bunny_sample.stl")

# create a cube mesh
cube = trimesh.creation.box(extents=(3, 3, 3))

# create a cylinder mesh
cylinder = trimesh.creation.cylinder(radius=1.0, height=2.0)

cylinder.show()