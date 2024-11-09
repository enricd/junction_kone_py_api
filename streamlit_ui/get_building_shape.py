import argparse
import requests
import json
from geopy.distance import geodesic

def get_user_input():
    parser = argparse.ArgumentParser(description='Process latitude and longitude.')
    parser.add_argument('latitude', type=float, help='Latitude value')
    parser.add_argument('longitude', type=float, help='Longitude value')
    args = parser.parse_args()
    return args.latitude, args.longitude

def get_building_nodes(lat, lon, mode="dict"):
    

    # Overpass API query to get ways and their nodes within a 10 meter radius
    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = f"""
    [out:json];
    (
      way(around:50,{lat},{lon});
      >;
    );
    out body;
    """
    response = requests.get(overpass_url, params={'data': overpass_query})
    data = response.json()

    # Extract ways and nodes
    ways = {}
    nodes = {}

    for element in data['elements']:
        if element['type'] == 'way':
            ways[element['id']] = element['nodes']
        elif element['type'] == 'node':
            nodes[element['id']] = {'lat': element['lat'], 'lon': element['lon']}

    # Function to calculate the distance between two points
    def calculate_distance(coord1, coord2):
        return geodesic(coord1, coord2).meters

    # Find the closest way
    closest_way = None
    min_distance = float('inf')

    for way_id, node_ids in ways.items():
        for node_id in node_ids:
            if node_id in nodes:
                node_coord = (nodes[node_id]['lat'], nodes[node_id]['lon'])
                distance = calculate_distance((lat, lon), node_coord)
                if distance < min_distance:
                    min_distance = distance
                    closest_way = way_id

    # Prepare the JSON data for the closest way
    if closest_way is not None:
        closest_way_data = {
            'way_id': closest_way,
            'nodes': []
        }
        for node_id in ways[closest_way]:
            if node_id in nodes:
                closest_way_data['nodes'].append({
                    'node_id': node_id,
                    'lat': nodes[node_id]['lat'],
                    'lon': nodes[node_id]['lon']
                })

        if mode == "json":
            # Write the closest way data to a JSON file
            with open('closest_way_1.json', 'w') as json_file:
                json.dump(closest_way_data, json_file, indent=4)
        elif mode == "dict":
            return closest_way_data

        print(f"The closest way ID is {closest_way} with a minimum distance of {min_distance} meters.")
    else:
        print("No ways found within the specified radius.")

if __name__ == "__main__":
    lat, lon = get_user_input()

    get_building_nodes(lat, lon)