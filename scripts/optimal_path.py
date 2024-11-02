import googlemaps
import networkx as nx
from itertools import permutations

def get_distances(stops):
    gmaps = googlemaps.Client(key='AIzaSyACh5R4n7riZPvRd7MHiXlByMvSjdP6zI4')
    
    origins = stops
    destinations = stops
    
    matrix = gmaps.distance_matrix(origins, destinations, mode="driving")

    distances = {}
    for i, row in enumerate(matrix['rows']):
        distances[stops[i]] = {}
        for j, element in enumerate(row['elements']):
            distances[stops[i]][stops[j]] = {
                'distance': element['distance']['value'], 
                'duration': element['duration']['value'] 
            }
    return distances


def create_graph(distances):
    graph = {}
    for origin, destinations in distances.items():
        graph[origin] = {}
        for destination, data in destinations.items():
            if origin != destination:
                graph[origin][destination] = data['distance']
    return graph



def find_shortest_path(graph_dict, origin, destination, waypoints):
    G = nx.DiGraph()
    for start, edges in graph_dict.items():
        for end, weight in edges.items():
            G.add_edge(start, end, weight=weight)

    unique_points = list(set([origin, destination] + [wp['pickup'] for wp in waypoints.values()] + [wp['drop'] for wp in waypoints.values()]))

    shortest_route = None
    min_distance = float('inf')
    for permutation in permutations(unique_points):
        if permutation[0] == origin and permutation[-1] == destination:
            current_distance = 0
            feasible_route = True
            for i in range(len(permutation) - 1):
                if permutation[i + 1] in G[permutation[i]]:
                    current_distance += G[permutation[i]][permutation[i + 1]]['weight']
                else:
                    feasible_route = False
                    break
            if feasible_route and current_distance < min_distance:
                valid_route = True
                for oid, wp in waypoints.items():
                    if permutation.index(wp['pickup']) > permutation.index(wp['drop']):
                        valid_route = False
                        break
                if valid_route:
                    min_distance = current_distance
                    shortest_route = permutation

    if shortest_route is None:
        return "No feasible route found", 0

    route_description = []
    visited_locations = set()
    for loc in shortest_route:
        if loc in visited_locations:
            continue
        visited_locations.add(loc)

        order_ids = []
        types = []
        for oid, wp in waypoints.items():
            if wp['pickup'] == loc:
                order_ids.append(oid)
                types.append('pickup')
            if wp['drop'] == loc:
                order_ids.append(oid)
                types.append('drop')

        route_description.append({
            'order_ids': ','.join(order_ids),
            'location': loc,
            'types': ','.join(types)
        })

    return route_description, min_distance





def generate_google_maps_url(origin, destination, waypoints):
    base_url = "https://www.google.com/maps/dir/"
    route_points = [origin] + waypoints + [destination]
    waypoints_str = '/'.join(route_points)
    return base_url + waypoints_str
