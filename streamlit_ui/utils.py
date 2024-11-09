import numpy as np
import trimesh
from shapely.geometry import Polygon, LineString
from stl import mesh
import plotly.graph_objects as go
import os
import matplotlib.pyplot as plt


def latlon2meters(lat, lon):
    origin_shift = 2 * np.pi * 6378137 / 2.0
    mx = lon * origin_shift / 180.0
    my = np.log(np.tan((90 + lat) * np.pi / 360.0)) / (np.pi / 180.0)
    my = float(my * origin_shift / 180.0)
    return mx, my


def building_shape_to_meters(geovertices):
    vertices = [latlon2meters(v["lat"], v["lon"]) for v in geovertices]
    vertices = [[round(x-vertices[0][0], 1), round(y-vertices[0][1], 1)] for x, y in vertices]
    return vertices


def create_3d_building(
    json_plan, 
    floor_height=3.0, 
    floors=1, 
    underground_floors=0,
    wall_thickness=0.2,
    debug=False,
):
    # Create the outer polygon
    outer_walls = json_plan["outer_walls"]
    outer_polygon = Polygon(outer_walls)
    if not outer_polygon.is_valid:
        raise ValueError("Invalid outer boundary.")

    # Define wall thickness
    # wall_thickness = 0.2  # Moved to function parameters

    # Create the inner polygon
    inner_polygon = outer_polygon.buffer(-wall_thickness)

    if inner_polygon.is_empty or not inner_polygon.is_valid:
        raise ValueError("Invalid wall thickness or building dimensions too small.")

    # Compute the wall area
    wall_area = outer_polygon.difference(inner_polygon)

    if wall_area.is_empty or not wall_area.is_valid:
        raise ValueError("The wall area could not be computed correctly.")

    floor_thickness = 0.2

    # Initialize heights
    above_ground_height = floors * floor_height if floors > 0 else 0
    underground_height = underground_floors * floor_height if underground_floors > 0 else 0
    total_height = above_ground_height + underground_height

    # Initialize elevator_polygon if it exists
    if "elevator" in json_plan:
        elevator_coords = json_plan["elevator"]
        elevator_polygon = Polygon(elevator_coords)
        if not elevator_polygon.is_valid:
            raise ValueError("Invalid elevator polygon.")
        # Subtract elevator from wall area
        wall_area = wall_area.difference(elevator_polygon)
        if wall_area.is_empty or not wall_area.is_valid:
            raise ValueError("Invalid wall area after subtracting elevator.")

    else:
        elevator_polygon = None  # For later checks

    # Only proceed if there are above-ground floors
    if floors > 0:
        # Extrude walls for above-ground floors from z=0 upwards
        walls_above_mesh = trimesh.creation.extrude_polygon(wall_area, height=above_ground_height)

        # Create floors and roof for above-ground floors
        floor_meshes_above = []
        for floor_level in range(floors + (1 if not debug else 0)):  # Include roof level
            z_level = floor_level * floor_height
            # For the roof, use the outer polygon
            floor_polygon = outer_polygon
            # Subtract elevator if it exists
            if elevator_polygon:
                floor_polygon = floor_polygon.difference(elevator_polygon)
                if floor_polygon.is_empty or not floor_polygon.is_valid:
                    raise ValueError(f"Invalid floor polygon at level {floor_level} after subtracting elevator shaft.")
            floor_mesh = trimesh.creation.extrude_polygon(floor_polygon, height=floor_thickness)
            floor_mesh.apply_translation([0, 0, z_level])
            floor_meshes_above.append(floor_mesh)

        # Process inner walls if they exist in the plan
        if "inner_walls" in json_plan:
            inner_walls_data = json_plan["inner_walls"]  # List of line segments [((x1, y1), (x2, y2)), ...]
            inner_walls_meshes = []
            for wall_line in inner_walls_data:
                start_point = wall_line[0]  # (x1, y1)
                end_point = wall_line[1]    # (x2, y2)

                # Create a LineString for the wall line
                wall_line_string = LineString([start_point, end_point])

                # Buffer the line to create a wall polygon with thickness
                wall_polygon = wall_line_string.buffer(wall_thickness / 2, cap_style=2)  # cap_style=2 for flat ends
                if wall_polygon.is_empty or not wall_polygon.is_valid:
                    raise ValueError("Invalid inner wall polygon created from line segment.")
                # Subtract elevator shaft from inner walls if they intersect
                if elevator_polygon:
                    if wall_polygon.intersects(elevator_polygon):
                        wall_polygon = wall_polygon.difference(elevator_polygon)
                        if wall_polygon.is_empty or not wall_polygon.is_valid:
                            continue  # Skip this inner wall if invalid after subtraction
                # Extrude the wall polygon to the building height
                wall_mesh = trimesh.creation.extrude_polygon(wall_polygon, height=above_ground_height)
                # Add the wall mesh to the list
                inner_walls_meshes.append(wall_mesh)
        else:
            inner_walls_meshes = []

        # Combine all meshes: outer walls, floors, and inner walls
        building_mesh_above = trimesh.util.concatenate(
            [walls_above_mesh] + floor_meshes_above + inner_walls_meshes
        )

        # Export Above-ground Mesh to STL
        building_mesh_above.export('building_above.stl')
        print("Above-ground building mesh exported to building_above.stl")

        # Export to glTF (binary .glb)
        building_mesh_above.export('building_above.glb')
        print("Building mesh exported to building_above.glb")

    if underground_floors > 0:
        # Extrude walls for underground floors from z=-underground_height upwards to z=0
        walls_underground_mesh = trimesh.creation.extrude_polygon(wall_area, height=underground_height)
        # Shift walls down to start from z = -underground_height
        walls_underground_mesh.apply_translation([0, 0, -underground_height])

        # Create floors for underground floors (no ceiling at z=0)
        floor_meshes_underground = []
        for floor_level in range(underground_floors):
            z_level = -(floor_level + 1) * floor_height  # Negative z-levels
            floor_polygon = outer_polygon
            # Subtract elevator if it exists
            if elevator_polygon:
                floor_polygon = floor_polygon.difference(elevator_polygon)
                if floor_polygon.is_empty or not floor_polygon.is_valid:
                    raise ValueError(f"Invalid floor polygon at level {floor_level} after subtracting elevator shaft.")
            floor_mesh = trimesh.creation.extrude_polygon(floor_polygon, height=floor_thickness)
            floor_mesh.apply_translation([0, 0, z_level])
            floor_meshes_underground.append(floor_mesh)

        # Process inner walls if they exist in the plan
        if "inner_walls" in json_plan:
            inner_walls_data = json_plan["inner_walls"]  # List of line segments [((x1, y1), (x2, y2)), ...]
            inner_walls_underground_meshes = []
            for wall_line in inner_walls_data:
                start_point = wall_line[0]  # (x1, y1)
                end_point = wall_line[1]    # (x2, y2)

                # Create a LineString for the wall line
                wall_line_string = LineString([start_point, end_point])

                # Buffer the line to create a wall polygon with thickness
                wall_polygon = wall_line_string.buffer(wall_thickness / 2, cap_style=2)  # cap_style=2 for flat ends
                if wall_polygon.is_empty or not wall_polygon.is_valid:
                    raise ValueError("Invalid inner wall polygon created from line segment.")
                # Subtract elevator shaft from inner walls if they intersect
                if elevator_polygon:
                    if wall_polygon.intersects(elevator_polygon):
                        wall_polygon = wall_polygon.difference(elevator_polygon)
                        if wall_polygon.is_empty or not wall_polygon.is_valid:
                            continue  # Skip this inner wall if invalid after subtraction
                # Extrude the wall polygon to the building height
                wall_mesh = trimesh.creation.extrude_polygon(wall_polygon, height=underground_height)
                # Shift walls down to start from z = -underground_height
                wall_mesh.apply_translation([0, 0, -underground_height])
                # Add the wall mesh to the list
                inner_walls_underground_meshes.append(wall_mesh)
        else:
            inner_walls_underground_meshes = []

        # Combine walls and floors into one mesh for underground
        building_mesh_underground = trimesh.util.concatenate(
            [walls_underground_mesh] + floor_meshes_underground + inner_walls_underground_meshes
        )

        # Export Underground Mesh to STL
        building_mesh_underground.export('building_under.stl')
        print("Underground building mesh exported to building_under.stl")

        # Export to glTF (binary .glb)
        building_mesh_underground.export('building_under.glb')
        print("Underground building mesh exported to building_under.glb")

    else:
        # Delete the underground building mesh if it exists
        try:
            os.remove("building_under.stl")
            os.remove("building_under.glb")
        except:
            pass

    # Create elevator shaft as an extruded polygon
    if elevator_polygon:
        elevator_mesh = trimesh.creation.extrude_polygon(elevator_polygon, height=total_height)
        # Shift the elevator mesh down to start from z = -underground_height
        elevator_mesh.apply_translation([0, 0, -underground_height])
        # Export elevator mesh to STL and GLB
        elevator_mesh.export('elevator.stl')
        elevator_mesh.export('elevator.glb')
        print("Elevator mesh exported to elevator.stl and elevator.glb")
    else:
        # Delete the elevator mesh if it exists
        try:
            os.remove("elevator.stl")
            os.remove("elevator.glb")
        except:
            pass


def get_stl_color(x):
    #two "attribute byte count" bytes at the end of every triangle to store a 15-bit RGB color
    #bits 0 to 4 are the intensity level for blue (0 to 31)
    #bits 5 to 9 are the intensity level for green (0 to 31)
    #bits 10 to 14 are the intensity level for red (0 to 31)
    sb = f'{x:015b}'[::-1]
    r = str(int(255/31*int(sb[:5],base=2)))
    g = str(int(255/31*int(sb[5:10],base=2)))
    b = str(int(255/31*int(sb[10:15],base=2)))
    r, g, b = (84, 164, 199)
    color = f'rgb({r},{g},{b})'
    return color

def get_stl_color_under(x):
    return 'rgb(214, 177, 135)'

def get_stl_color_elevator(x):
    return 'rgb(255, 0, 0)'


def stl2mesh3d(stl_file, type="above"):
    stl_mesh = mesh.Mesh.from_file(stl_file)
    # stl_mesh is read by nympy-stl from a stl file; it is  an array of faces/triangles (i.e. three 3d points) 
    # this function extracts the unique vertices and the lists I, J, K to define a Plotly mesh3d
    p, q, r = stl_mesh.vectors.shape #(p, 3, 3)
    # the array stl_mesh.vectors.reshape(p*q, r) can contain multiple copies of the same vertex;
    # extract unique vertices from all mesh triangles
    vertices, ixr = np.unique(stl_mesh.vectors.reshape(p*q, r), return_inverse=True, axis=0)
    I = np.take(ixr, [3*k for k in range(p)])
    J = np.take(ixr, [3*k+1 for k in range(p)])
    K = np.take(ixr, [3*k+2 for k in range(p)])
    if type == "above":
        color_f = get_stl_color
    elif type == "under":
        color_f = get_stl_color_under
    elif type == "elevator":
        color_f = get_stl_color_elevator
    facecolor = np.vectorize(color_f)(stl_mesh.attr.flatten())
    x, y, z = vertices.T
    trace = go.Mesh3d(x=x, y=y, z=z, i=I, j=J, k=K, facecolor=facecolor, opacity=0.5, vertexcolorsrc='(0,0,0)')
    # optional parameters to make it look nicer
    trace.update(flatshading=True, lighting_facenormalsepsilon=0, lighting_ambient=0.7)

    return trace

def plan2img(outer_boundary):
    # create a plot image of the polygon of the building plan
    plt.figure()
    plt.plot([x for x, y in outer_boundary], [y for x, y in outer_boundary], 'b-')
    # remove axis
    plt.axis('off')
    # remove margins
    plt.savefig('plan.png', bbox_inches='tight', pad_inches=0)




if __name__ == "__main__":
    # geovertices = [
    #     {"lat": 60.16175, "lon": 24.90411},
    #     {"lat": 60.16175, "lon": 24.90421},
    #     {"lat": 60.16185, "lon": 24.90421},
    #     {"lat": 60.16185, "lon": 24.90411},
    # ]
    # print(building_shape_to_meters(geovertices))


    json_plan = {
        "outer_walls": [(0, 0), (10, 0), (10, 20), (-10, 20), (-10, 10), (0, 10)],
        "inner_walls": [[(-5, 10), (-5, 20)], [(-5, 15), (10, 15)]],
        "elevator": [(5, 12), (7, 12), (7, 14), (5, 14)],
    }

    create_3d_building(json_plan, floor_height=3.0, floors=4, underground_floors=3, debug=False)

