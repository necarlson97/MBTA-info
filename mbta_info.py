# TODO DOC IMPORTS
import requests
import math
import sys


# TODO DOC & REMOVE
API_KEY = 'e0bf1c55aaa243abb06d15ab0a05950b'


def call_mbta_api(endpoint, filter_type, filter_value):
    """
    TODO DOC
    """
    url = f'https://api-v3.mbta.com/{endpoint}'
    params = {
        f'filter[{filter_type}]': filter_value
    }

    # Add the optional api key
    if API_KEY is not None:
        params['api_key'] = API_KEY

    res = requests.get(url=url, params=params)
    res_json = res.json()
    data = res_json.get('data')

    # In case the api did not return as expected,
    # throw a more readable answer
    if data is None:
        raise ValueError(f"Expected 'data' entry in mbta api response.\n"
                         f"Called: {url}\n"
                         f"Recieved: {res_json}")
    return data


def get_routes_data():
    """
    TODO DOC
    """
    # Call the routes endpoint, filtering on route types 0 and 1
    # (light rail and heavy rail)
    return call_mbta_api('routes', 'type', '0,1')


def get_data_dict(data, kept_attributes=None):
    """
    TODO DOC
    """
    attrs = data.get('attributes', {})
    return {k: v for k, v in attrs.items()
            if kept_attributes is None or
            k in kept_attributes}


def get_stops_data(route_id):
    """
    TODO DOC
    """
    data = call_mbta_api('stops', 'route', route_id)

    kept_keys = ['name']
    stops_dict = {d.get('id'): get_data_dict(d, kept_keys)
                  for d in data}
    return stops_dict


def get_subway_data():
    """
    TODO DOC
    """
    data = get_routes_data()
    # Here we place the data into a dictionary, key-ing each line on it's
    # id field (which can be assumed to be unique).
    # We filter out only the desired attributes to keep the dictionary
    # smaller and more easily human readable
    kept_keys = ['long_name']
    data_dict = {d.get('id'): get_data_dict(d, kept_keys) for d in data}

    # For each route, add a 'stops_ict' entry which contains
    # the stop_id -> stop_data for all stops on this route.
    # NOTE: see get_stops_data for additional details on what is considered
    # 'stop_data'
    for route_id, route_data in data_dict.items():
        stops_data = get_stops_data(route_id)
        route_data['stops_dict'] = stops_data

    return data_dict


def print_names(data_dict):
    """
    TODO DOC
    """

    # Small helper function to be used in the list comprehension for
    # extracting long names
    def get_long_name(route_data):
        return route_data.get('long_name')

    long_names = [get_long_name(r) for r in data_dict.values()]

    print('Subway Route Names:')
    print(', '.join(long_names))
    print()


def print_system_info(data_dict):

    # For calculating the minimum and maximum route by stop count
    min_stops = math.inf
    min_route = ''
    max_stops = 0
    max_route = ''

    # For calculating which routes share stops
    stop_routes = {}

    for route_id, route_data in data_dict.items():
        route_name = route_data.get('long_name')
        stops_dict = route_data.get('stops_dict', {})
        stop_count = len(stops_dict)

        if stop_count > max_stops:
            max_stops = stop_count
            max_route = route_name

        if stop_count < min_stops:
            min_stops = stop_count
            min_route = route_name

        for stop_id, stop_dict in stops_dict.items():
            stop_name = stop_dict.get('name')
            stop_routes.setdefault(stop_name, []).append(route_name)

    # Get only the stops which were on more than 1 route
    stop_routes = {k: v for k, v in stop_routes.items()
                   if len(v) > 1}

    print('Additional Route Info:')
    print(f'1. Longest route = {max_route} ({max_stops} stops)')
    print(f'2. Shortest route = {min_route} ({min_stops} stops)')
    print(f'3. Connecting stops =')
    for stop_name, route_names in stop_routes.items():
        print(f'  {stop_name}:', ', '.join(route_names))
    print()


def print_connecting_routes(data_dict, start_name, end_name):
    """
    TODO DOC
    """

    stop_routes = {}
    route_stops = {}
    for route_id, route_data in data_dict.items():
        route_name = route_data.get('long_name')
        stops_dict = route_data.get('stops_dict', {})

        for stop_id, stop_dict in stops_dict.items():
            stop_name = stop_dict.get('name')
            stop_routes.setdefault(stop_name, []).append(route_name)
            route_stops.setdefault(route_name, []).append(stop_name)

    routes = BFS(route_stops, stop_routes, start_name, end_name)

    print(f'Routes to get from {start_name} to {end_name}:')
    print(', '.join(routes))
    print()


def BFS(route_stops, stop_routes, start_name, end_name):
    """
    TODO DOC
    """

    if start_name not in stop_routes:
        raise ValueError(f'No station found named {start_name}')

    if end_name not in stop_routes:
        raise ValueError(f'No station found named {end_name}')

    queue = [start_name]
    visited = []

    while True:

        if end_name in queue:
            break

        if not queue:
            raise ValueError(f'No trip found between '
                             f'{start_name} and {end_name}')

        curr_stop_name = queue.pop(0)

        for route_name in stop_routes[curr_stop_name]:
            if route_name not in visited:
                queue.extend(route_stops[route_name])
                visited.append(route_name)

    return visited


CLI_CALL = 'python mbta_info'
HELP_TXT = f"""
A comand line tool for printing information on the mbta subway system.
See https://api-v3.mbta.com/docs/swagger/index.html for more details on the
api used (in particular: .../routes)

Uses:
    {CLI_CALL} names - Print the 'Long Name' of each subway
        Ex: "Red Line, Orange Line..."
    {CLI_CALL} info - Print additional info about the subway system
        Ex: "1. Longest route = ...
             2. Shortest route = ...
             3. Connecting stops = ...
    {CLI_CALL} directions "{{starting station name}}" "{{ending station name}}" -
        Calculates a set of routes to get one to their destination.
        NOTE: Does NOT find the shortest path.
    {CLI_CALL} example - Call each command (with example inputs)
"""  # noqa

if __name__ == '__main__':
    """
    TODO ARGS AND HELP TEXT
    """

    def get_arg(n):
        return None if len(sys.argv) < n + 1 else sys.argv[n]

    arg1 = get_arg(1)
    arg2 = get_arg(2)
    arg3 = get_arg(3)

    # A helper function to curry the arguments into a
    # 'print_connecting_routes' function (as well as catch missing args)
    def curried_directions(data_dict):
        if arg2 is None or arg3 is None:
            print('Please input both starting and ending destination.')
            print(f'Was given: ({arg2} {arg3})')
            print(HELP_TXT)
        else:
            print_connecting_routes(data_dict, arg2, arg3)

    # A helper function to call all of the commands, and display their
    # results as an example to the user
    def curried_examples(data_dict):
        print('Calling all commands (with example inputs):')
        print_names(data_dict)
        print_system_info(data_dict)
        print_connecting_routes(data_dict, 'Forest Hills', 'Jackson Square')
        print_connecting_routes(data_dict, 'Forest Hills', 'Haymarket')
        print_connecting_routes(data_dict, 'Forest Hills', 'Government Center')
        print_connecting_routes(data_dict, 'Forest Hills', 'Kenmore')

    arg_calls = {
        'names': print_names,
        'info': print_system_info,
        'directions': curried_directions,
        'example': curried_examples
    }

    if arg1 not in arg_calls:
        print(f'Please choose command from {list(arg_calls.keys())}.')
        print(f'Was given: ({arg1})')
        print(HELP_TXT)
    else:
        func = arg_calls[arg1]
        data_dict = get_subway_data()
        func(data_dict)
