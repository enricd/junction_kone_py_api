import trimesh
import numpy as np

def create_extruded_polygon(vertices, height=3):
    # Create a 2D polygon
    polygon = trimesh.path.Path2D(vertices)

    # Extrude the 2D polygon to create a 3D object
    extruded = polygon.extrude(height)

    return extruded

# Example vertices of a polygon (square in this case)
vertices = np.array([
    [0, 0],
    [1, 0],
    [1, 1],
    [0, 1]
])

# Height of the extrusion
height = 3.0

# Create the 3D object
extruded_polygon = create_extruded_polygon(vertices, height)

# Save the 3D object to a file (optional, for visualization)
extruded_polygon.export('extruded_polygon.obj')