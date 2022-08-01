from typing import Dict, List, Tuple
from unicodedata import category

import pandas as pd
import copy
from geopy.distance import geodesic
import copy
import preprocessing.backend as backend
import preprocessing.battery as battery
import preprocessing.clustering as clustering


def _get_intermediate_points(request_values):
    """Collecting intermediate points from user input if there are any"""
    intermediate_points = []
    keys = request_values.keys()
    matching = list(filter(lambda s: 'intermediate' in s, keys))
    for value in matching:
        intermediate_points.append(request_values[value])
    return intermediate_points

def collect_user_inputs(request_values):
    """Collecting values from user input and storing it as separate variables for use later"""
    start_point = request_values.get("start-point")
    end_point = request_values.get("end-point")
    intermediate_points = _get_intermediate_points(request_values)
    range_start = request_values.get("range-start")
    range_arrival = request_values.get("range-arrival")
    start_time = request_values.get("start-time")
    start_time = f"{start_time}:00"
    start_date = request_values.get("start-date")
    poi_radius = request_values.get("poi-radius")
    range_ev = request_values.get("range-ev")

    return start_point, end_point, range_start, range_arrival, start_time, start_date, intermediate_points, poi_radius, range_ev

def search_input(request_values):
    """Collecting values from user input for search tab function (Not in use)"""
    search_point = request_values.get("search-point")
    return search_point

def get_nearest_charging_stations(
    search_point: List[Tuple[float, float]], bng_dat_path: str = "./resources/bng_df.csv"
    ) -> pd.DataFrame: 

    """Function find nearest charging stations given a point (Not in use)"""

    stations = pd.read_csv(bng_dat_path)
    nearest_df = clustering.nearest_charging_stations(search_point, stations)
    return nearest_df


# def get_lat_long_from_coordinates(
#     coordinates: Dict[str, object]
# ) -> Tuple[float, float]:
#     """Function to get latitude and longitude from the geojson object that is received from the API call"""
#     try:
#         lon = coordinates["features"][0]["geometry"]["coordinates"][0]
#         lat = coordinates["features"][0]["geometry"]["coordinates"][1]
#         return lat, lon
#     except IndexError:
#         return 0.0, 0.0

def get_lat_long_from_coordinates(
    coordinates: Dict[str, object]
) -> Tuple[float, float]:
    """Function to get latitude and longitude from the geojson object that is received from the API call"""
    try:
        lon = coordinates["items"][0]["position"]["lng"]
        lat = coordinates["items"][0]["position"]["lat"]
        return lat, lon
    except IndexError:
        return 0.0, 0.0


def get_markers(
    origin_lat: float, origin_lon: float, destination_lat: float, destination_lon: float
) -> str:
    orig_address = backend.get_address(origin_lat, origin_lon)
    dest_address = backend.get_address(destination_lat, destination_lon)
    """Function to create a marker list to include marker positions of origin and destination"""
    
    markers = ""
    markers += "var {idd} = L.marker([{latitude}, {longitude}]);\
                                {idd}.addTo(map);".format(
        idd="origin",
        latitude=origin_lat,
        longitude=origin_lon,
    )

    markers += """{idd}.bindPopup("{address}");""".format(idd=f"origin", address = f"{orig_address}")
    
    markers += "var {idd} = L.marker([{latitude}, {longitude}]);\
                                {idd}.addTo(map);".format(
        idd="destination",
        latitude=destination_lat,
        longitude=destination_lon,
    )
    markers += """{idd}.bindPopup("{address}");""".format(idd=f"destination", address = f"{dest_address}")
    
    return markers


def get_markers_intermediate(markers, lst):
    """Function to add intermediate markers to existing list of markers"""
    weather = backend.get_weather(lst[0], lst[1])
    markers += "var {idd} = L.marker([{latitude}, {longitude}]);\
                                {idd}.addTo(map);".format(
        idd=f"intermediate{lst[0]+1}",
        latitude=lst[1],
        longitude=lst[2],
    )
    markers += """{idd}.bindPopup("{data}");""".format(idd=f"intermediate{lst[0]+1}", data = f"Intermediate Point {lst[0]+1}, Weather: {weather}")
    return markers


def compute_midpoint(lat1, lon1, lat2, lon2) -> Tuple[float, float]:
    """Computing midpoint of origin and desination"""
    return (lat1 + lat2) / 2, (lon1 + lon2) / 2



def get_stations_data(
    point_list: List[Tuple[float, float]], 
    origin_lat: float, 
    origin_lon: float,
    dest_lat: float,
    dest_lon: float,
    bng_dat_path: str = "./resources/bng_df.csv", 
    
) -> pd.DataFrame:
    path = pd.DataFrame(point_list, columns=["lat", "lng"])
    """Function to get the stations nearby path coordinates"""

    stations = pd.read_csv(bng_dat_path)
    stations = clustering.dimension_reduction(path, origin_lat, origin_lon, dest_lat, dest_lon, stations)
    return stations

def get_clustering_data(
    point_list: List[Tuple[float, float]], 
    origin_lat: float, 
    origin_lon: float,
    dest_lat: float,
    dest_lon: float,
    stations: pd.DataFrame,
    bng_dat_path: str = "./resources/bng_df.csv", 
    
) -> pd.DataFrame:
    path = pd.DataFrame(point_list, columns=["lat", "lng"])

    """Function to clustering stations near path"""

    # stations = pd.read_csv(bng_dat_path)
    # stations = clustering.dimension_reduction(path, origin_lat, origin_lon, dest_lat, dest_lon, stations)
    df = clustering.clustering_algo(path, stations)
    return df

def process_inputs_own_rest(
    start_point: str,
    rest_point: str,
    end_point:str,
    range_start: float,
    range_arrival: int,
    start_time: str,
    start_date: str,
    intermediate_points: list,
    total_distance: float,
    range_ev: float,
    bng_dat_path: str = "./resources/bng_df.csv",

):  
    """Function to process inputs to find optimal charging stations where user has provided a rest input"""

    range_ev = float(range_ev) #Converting string input of range_ev to float
    origin = backend.get_coordinates(start_point) # Getting coordinates from address input, origin
    origin_lat, origin_lon = get_lat_long_from_coordinates(origin) # Getting latitude and longitude from address

    rest_place = backend.get_coordinates(rest_point) # Getting coordinates from address input, rest place
    rest_lat, rest_lon = get_lat_long_from_coordinates(rest_place) # Getting latitude and longitude from address

    accom_lat, accom_lon = rest_lat, rest_lon # Storing the place that the user wants to rest as accom_lat and accom_lon

    destination = backend.get_coordinates(end_point) # Getting coordinates from address input, destination
    destination_lat, destination_lon = get_lat_long_from_coordinates(destination) # Getting latitude and longitude from address

    intermediate_points_coords = [] # Empty list to store intermediate points 
    
    for i in range(len(intermediate_points)): # For loop to get coordinates of intermediate points if there are any
        location = intermediate_points[i] # Accessing an intermediate point 
        coords = backend.get_coordinates(location) # Getting coordinates from address input, intermediate point
        intermediate_lat, intermediate_lon = get_lat_long_from_coordinates(coords) # Getting latitude and longitude from address
        intermediate_points_coords.append([i, intermediate_lat, intermediate_lon]) # Storing intermediate points in list
    
    
    closest_df = clustering.near_points([[rest_lat, rest_lon]], stations = pd.read_csv('./resources/bng_df.csv')) # Finding nearest charging station to rest point

    closest_df["lat_lon"] = list(zip(closest_df.Latitude, closest_df.Longitude)) # Combining latitude and longitude to single column
    near = closest_df.loc[closest_df.Label == "Closest"] # Getting the closest points

    point = [[rest_lat,rest_lon]] # Creating a 2D array using the rest place coordinates
     
    dists = near['lat_lon'].apply(lambda x: geodesic(point, x).km) # Finding the distance between rest place and the nearby charging stations

    closest = near.loc[dists.idxmin()] # Finding the shortest distance in the dataframe

    rest_lat, rest_lon = closest["Latitude"], closest["Longitude"] # Replacing rest lat and rest lon to the nearest station coordinates (For path query in API)

    
    

    if len(intermediate_points_coords) > 0: # If there are intermediate points, add to point list for query later
        points = []
        for i in intermediate_points_coords:
            points.append([i[1],i[2]])
        points.insert(0, [origin_lat, origin_lon])
        points.append([rest_lat, rest_lon])
        points2 = copy.deepcopy(points)
        point_list, distance_travelled_by_rest_place, time = backend.get_route_many(points) # Get route for origin, intermediate points and rest place (Default)
        point_list_alt_1, distance_travelled_by_rest_place_alt_1, time_alt_1 = backend.get_route_many_short(points2) # Get route for origin, intermediate points and rest place (Short)

        points.append([destination_lat, destination_lon]) # Adding destination to list of points
        points2 = copy.deepcopy(points)
        point_list_complete, dist_complete, time_complete = backend.get_route_many(points)  # Get route for origin, intermediate points, rest place and destination (Default)
        point_list_complete_alt, dist_complete_alt, time_complete_alt = backend.get_route_many_short(points2) # Get route for origin, intermediate points, rest place and destination (Short)
    else: # Creating points list for query later, when there are no intermediate points
        points = [] 
        points.insert(0, [origin_lat, origin_lon]) 
        points.append([rest_lat, rest_lon])
        points.append([destination_lat, destination_lon])


        # Get route for origin and rest place (Default)
        point_list, distance_travelled_by_rest_place, time = backend.get_route( 
            origin_lat, origin_lon, rest_lat, rest_lon
        )
         # Get route for origin and rest place (Short)
        point_list_alt_1, distance_travelled_by_rest_place_alt_1, time_alt_1 = backend.get_route_short(
            origin_lat, origin_lon, rest_lat, rest_lon
        )
        points2 = copy.deepcopy(points)
        # Get route for origin, rest place and destination (Default)
        point_list_complete, dist_complete, time_complete = backend.get_route_many(points)
        # Get route for origin, rest place and destination (Short)
        point_list_complete_alt, dist_complete_alt, time_complete_alt = backend.get_route_many_short(points2)

    # Getting stations that are near path   
    stations = get_stations_data(point_list, origin_lat, origin_lon, destination_lat, destination_lon, bng_dat_path)
    
    # Creating markers list using origin and destination
    markers = get_markers(origin_lat, origin_lon, destination_lat, destination_lon)
    
    # Adding intermediate marker positions to marker list
    for i in intermediate_points_coords:
        markers = get_markers_intermediate(markers, i)

    # Computing mid lat and mid lon
    mid_lat, mid_lon = compute_midpoint(
        origin_lat, origin_lon, destination_lat, destination_lon
    )

    # Clustering data for path coordinates till rest place (Default)
    df = get_clustering_data(point_list, origin_lat, origin_lon, destination_lat, destination_lon, stations, bng_dat_path)
    # Clustering data for path coordinates till rest place (Short)
    df_alt_1 = get_clustering_data(point_list_alt_1, origin_lat, origin_lon, destination_lat, destination_lon,stations, bng_dat_path)
    # Clustering data for path coordinates till destination (Default)
    df_complete = get_clustering_data(point_list_complete, origin_lat, origin_lon, destination_lat, destination_lon, stations, bng_dat_path)
     # Clustering data for path coordinates till destination (Short)
    df_complete_alt = get_clustering_data(point_list_complete_alt, origin_lat, origin_lon, destination_lat, destination_lon, stations, bng_dat_path)
    
    
    # Defining variables required for battery script
    initial_soc = float(range_start)
    final_threshold = float(range_arrival)
    total_time = 0
    total_distance = total_distance
    min_threshold = 15
    dist_travelled = 0
    stop = 1
    range_needed = 0
    ave_speed = 40
    trip_start = start_time

    # Runing battery script for own_rest using default path
    lst = battery.station_coordinates_own_rest(
        df, 
        initial_soc, 
        min_threshold, 
        total_distance, 
        dist_travelled, 
        range_ev, 
        stop, 
        final_threshold, 
        range_needed,
        ave_speed, 
        start_time, 
        trip_start, 
        total_time, 
        rest_lat, 
        rest_lon, 
        distance_travelled_by_rest_place,
        df_complete)

     # Runing battery script for own_rest using shorter path
    lst_alt_1 = battery.station_coordinates_own_rest(
        df_alt_1,
        initial_soc,
        min_threshold,
        total_distance,
        dist_travelled,
        range_ev,
        stop,
        final_threshold,
        range_needed,
        ave_speed,
        start_time,
        trip_start,
        total_time,
        rest_lat, 
        rest_lon, 
        distance_travelled_by_rest_place_alt_1,
        df_complete_alt
    )

    # If the trip is incomplete, meaning not enough charging stations, print message and return None
    if lst == "Trip cannot be completed as no charging station is available in the vicinity":
        return None
    # If the trip can be completed with no charging, it falls under this case since there are no coordinates inserted from script
    if type(lst) == str or type(lst_alt_1) == str:
            #Data processing of dictionary from battery script to individual variables to be rendered in HTML later
            night_travel = False
            time_end = 0
            if len(intermediate_points_coords) < 1:
                point_list, distance, time = backend.get_route_short(origin_lat, origin_lon, destination_lat, destination_lon)
        
            else:
                point_list, distance, time = backend.get_route_many_short(points)

            lst = [lst]
            idx_lst = [0]
            lst = dict(zip(idx_lst, lst))
                    
            lst_coord = []
            lst2 = lst_coord
            cs = copy.deepcopy(lst2)
            marker_lst = []
            lst2.insert(0, [origin_lat, origin_lon])
            lst2.append([destination_lat, destination_lon])
            idx = [i for i in range(len(lst2))]
            res = {idx[i]: lst2[i] for i in range(len(idx))}
            last_leg = {0: [initial_soc, distance, initial_soc - (distance/ (range_ev/100))]}


            marker_lst.append("L.marker([{latitude}, {longitude}])".format(latitude=origin_lat,\
                                                                                            longitude=origin_lon,
                                                                                                    ))
            marker_lst.append("L.marker([{latitude}, {longitude}])".format(latitude=destination_lat,\
                                                                                               longitude=destination_lon,
                                                                                                    ))
            last_leg2 = []
            rest_charge_last_leg = []

            chargingtime = []
            for i in range(1, len(lst)+1):
                chargingtime.append(lst[i][5])
            cs_df = pd.DataFrame(cs, columns = ["Latitude", "Longitude"])
            cs_df["Charging_Time"] = chargingtime
            point_list_df = pd.DataFrame(point_list, columns = ["Latitude", "Longitude"])
            cs_df = backend.get_nearest_point(point_list_df, cs_df)
            weather_df = clustering.add_time_column(point_list_df, cs_df, f"{start_date} {start_time}")
            weather_df = backend.get_weather(weather_df)
            markers = backend.get_severe_weather(weather_df, markers)


            night_travel_alt = False
            time_end_alt = 0
            if len(intermediate_points_coords) < 1:
                point_list_alt_1, distance_alt_1, time_alt_1 = backend.get_route_short(origin_lat, origin_lon, destination_lat, destination_lon)
        
            else:
                point_list_alt_1, distance_alt_1, time_alt_1 = backend.get_route_many_short(points)
        
            lst_alt_1 = [lst_alt_1]
            idx_lst_alt = [0]
            lst_alt_1 = dict(zip(idx_lst_alt, lst_alt_1))
                    
            lst_coord_alt = []
            lst2_alt = lst_coord_alt
            cs_alt = copy.deepcopy(lst2_alt)
            marker_lst_alt = []
            lst2_alt.insert(0, [origin_lat, origin_lon])
            lst2_alt.append([destination_lat, destination_lon])
            idx_alt = [i for i in range(len(lst2_alt))]
            res_alt = {idx_alt[i]: lst2_alt[i] for i in range(len(idx_alt))}
            last_leg_alt = {0: [initial_soc, distance_alt_1, initial_soc - (distance_alt_1/ (range_ev/100))]}


            marker_lst_alt.append("L.marker([{latitude}, {longitude}])".format(latitude=origin_lat,\
                                                                                            longitude=origin_lon,
                                                                                                    ))
            marker_lst_alt.append("L.marker([{latitude}, {longitude}])".format(latitude=destination_lat,\
                                                                                            longitude=destination_lon,
                                                                                                    ))

            last_leg2_alt = []
            rest_charge_last_leg_alt = []
            markers_alt = markers
            chargingtime = []
            for i in range(1, len(lst)+1):
                chargingtime.append(lst[i][5])
            cs_df_alt = pd.DataFrame(cs_alt, columns = ["Latitude", "Longitude"])
            cs_df_alt["Charging_Time"] = chargingtime
            point_list_df_alt = pd.DataFrame(point_list_alt_1, columns = ["Latitude", "Longitude"])
            cs_df = backend.get_nearest_point(point_list_df_alt, cs_df_alt)
            weather_df_alt = clustering.add_time_column(point_list_df_alt, cs_df_alt, f"{start_date} {start_time}")
            weather_df_alt = backend.get_weather(weather_df_alt)
            markers_alt = backend.get_severe_weather(weather_df_alt, markers_alt)
            

            return (
            marker_lst,
            markers,
            mid_lat,
            mid_lon,
            point_list,
            distance,
            time,
            initial_soc,
            final_threshold,
            start_time,
            lst,
            res,
            last_leg,
            night_travel,
            time_end,
            last_leg2,
            rest_charge_last_leg,
            
            
            marker_lst_alt,
            markers_alt,
            mid_lat,
            mid_lon,
            point_list_alt_1,
            distance_alt_1,
            time_alt_1,
            initial_soc,
            final_threshold,
            start_time,
            lst_alt_1,
            res_alt,
            last_leg_alt,
            night_travel_alt,
            time_end_alt,
            last_leg2_alt,
            rest_charge_last_leg_alt)

    else:
        #Data processing of dictionary from battery script to individual variables to be rendered in HTML later

        lstcopy = copy.deepcopy(lst)
        lst = copy.deepcopy(lst[1][0])

        del lstcopy[list(lstcopy.keys())[0]]


        keys = list(lst.keys())
        time_end = lst[keys[-1]][0]
        night_travel = lst[keys[-1]][1]
        if len(keys) > 1:
            last_leg = [lst[keys[-2]]]
            idx_lst = [0]
            last_leg = dict(zip(idx_lst, last_leg))

            lst3 = copy.deepcopy(lstcopy)

            del lst3[list(lst3.keys())[-1]]

            rest_charge_last_leg = lst3[list(lst3.keys())[-1]]
            del lst3[list(lst3.keys())[-1]]

            del lst[keys[-1]]
            keys = keys[:-1]
            del lst[keys[-1]]
            marker_lst = []
            lst_coord = []

            for i in lst.keys():
                id = "stop" + str(i)
                markers += "var {idd} = L.marker([{latitude}, {longitude}],markerOptions_CS);\
                                                {idd}.addTo(map);".format(idd=id, latitude=float(lst[i][2]),\
                                                                                        longitude=float(lst[i][3]),
                                                                                                )

                marker_lst.append("L.marker([{latitude}, {longitude}])".format(latitude=float(lst[i][2]),\
                                                                                        longitude=float(lst[i][3]),
                                                                                                )
                                )
                lst_coord.append([lst[i][2],lst[i][3]])



            for i in lst3.keys():
                id = "stoprest" + str(i)
                markers += "var {idd} = L.marker([{latitude}, {longitude}],markerOptions_CS);\
                                                {idd}.addTo(map);".format(idd=id, latitude=float(lst3[i][1]),\
                                                                                        longitude=float(lst3[i][2]),
                                                                                                )
                                                                    
                marker_lst.append("L.marker([{latitude}, {longitude}])".format(latitude=float(lst3[i][1]),\
                                                                                        longitude=float(lst3[i][2]),
                                                                                                )
                                )
                lst_coord.append([lst3[i][1],lst3[i][2]])

            
            rest_address = backend.get_address(accom_lat, accom_lon)
            id = "restlocationbyuser"
            markers += "var {idd} = L.marker([{latitude}, {longitude}],markerOptions_Hotel);\
                                                {idd}.addTo(map);".format(idd=id, latitude=float(accom_lat),\
                                                                                        longitude=float(accom_lon),
                                                                               
                                                                                         )
            name_accom = f"{rest_address}"                                                                        
            markers += """{idd}.bindPopup("{data}");""".format(idd=id, data = name_accom)




            last_leg2 = lst3

            lst2 = lst_coord
            cs = copy.deepcopy(lst2)
            lst2.insert(0, [origin_lat, origin_lon])
            if len(intermediate_points_coords) > 0:
                for i in intermediate_points_coords:
                    lst2.append([i[1], i[2]])
            lst2.append([destination_lat, destination_lon])
            idx = [i for i in range(len(lst2))]
            res = {idx[i]: lst2[i] for i in range(len(idx))}
            point_list, distance, time = backend.get_route_many(lst2)

            chargingtime = []
            for i in range(1, len(lst)+1):
                chargingtime.append(lst[i][5])
            cs_df = pd.DataFrame(cs, columns = ["Latitude", "Longitude"])
            cs_df["Charging_Time"] = chargingtime
            point_list_df = pd.DataFrame(point_list, columns = ["Latitude", "Longitude"])
            cs_df = backend.get_nearest_point(point_list_df, cs_df)
            weather_df = clustering.add_time_column(point_list_df, cs_df, f"{start_date} {start_time}")
            weather_df = backend.get_weather(weather_df)
            markers = backend.get_severe_weather(weather_df, markers)

            #For alternative route1
            lstcopy_alt = copy.deepcopy(lst_alt_1)
            lst_alt_1 = copy.deepcopy(lst_alt_1[1][0])
 
            del lstcopy_alt[list(lstcopy_alt.keys())[0]]


            keys_alt = list(lst_alt_1.keys())
            time_end_alt = lst_alt_1[keys_alt[-1]][0]
            night_travel_alt = lst_alt_1[keys_alt[-1]][1]
            if len(keys_alt) > 1:
                last_leg_alt = [lst_alt_1[keys_alt[-2]]]
                idx_lst_alt = [0]
                last_leg_alt = dict(zip(idx_lst_alt, last_leg_alt))
                
                lst3_alt = copy.deepcopy(lstcopy_alt)
  
                del lst3_alt[list(lst3_alt.keys())[-1]]

                rest_charge_last_leg_alt = lst3_alt[list(lst3_alt.keys())[-1]]
                del lst3_alt[list(lst3_alt.keys())[-1]]

                del lst_alt_1[keys_alt[-1]]
                keys_alt = keys_alt[:-1]
                del lst_alt_1[keys_alt[-1]]
                marker_lst_alt = []
                lst_coord_alt = []
                
                markers_alt = markers

                for i in lst_alt_1.keys():
                    id = "stop_alt" + str(i)
                    markers_alt += "var {idd} = L.marker([{latitude}, {longitude}],markerOptions_CS);\
                                                    {idd}.addTo(map);".format(idd=id, latitude=float(lst[i][2]),\
                                                                                            longitude=float(lst[i][3]),
                                                                                                    )

                    marker_lst_alt.append("L.marker([{latitude}, {longitude}])".format(latitude=float(lst[i][2]),\
                                                                                            longitude=float(lst[i][3]),
                                                                                                    )
                                    )
                    lst_coord_alt.append([lst[i][2],lst[i][3]])



                for i in lst3_alt.keys():
                    id = "stoprest_alt" + str(i)
                    markers_alt += "var {idd} = L.marker([{latitude}, {longitude}],markerOptions_CS);\
                                                    {idd}.addTo(map);".format(idd=id, latitude=float(lst3[i][1]),\
                                                                                            longitude=float(lst3[i][2]),
                                                                                                    )
                                                                        
                    marker_lst_alt.append("L.marker([{latitude}, {longitude}])".format(latitude=float(lst3[i][1]),\
                                                                                            longitude=float(lst3[i][2]),
                                                                                                    )
                                    )
                    lst_coord_alt.append([lst3[i][1],lst3[i][2]])


                rest_address = backend.get_address(accom_lat, accom_lon)
                id = "restlocationbyuser"
                markers_alt += "var {idd} = L.marker([{latitude}, {longitude}],markerOptions_Hotel);\
                                                    {idd}.addTo(map);".format(idd=id, latitude=float(accom_lat),\
                                                                                            longitude=float(accom_lon),
                                                                                    
                                                                                                    )
                name_accom = f"{rest_address}"                                                                        
                markers_alt += """{idd}.bindPopup("{data}");""".format(idd=id, data = name_accom)


                last_leg2_alt = lst3_alt

                lst2_alt = lst_coord_alt
                cs_alt = copy.deepcopy(lst2_alt)
                lst2_alt.insert(0, [origin_lat, origin_lon])
                if len(intermediate_points_coords) > 0:
                    for i in intermediate_points_coords:
                        lst2_alt.append([i[1], i[2]])
                lst2_alt.append([destination_lat, destination_lon])
                idx_alt = [i for i in range(len(lst2_alt))]
                res_alt = {idx_alt[i]: lst2_alt[i] for i in range(len(idx_alt))}
                point_list_alt_1, distance_alt_1, time_alt_1 = backend.get_route_many(lst2_alt)
                
                chargingtime = []
                for i in range(1, len(lst)+1):
                    chargingtime.append(lst[i][5])
                cs_df_alt = pd.DataFrame(cs_alt, columns = ["Latitude", "Longitude"])
                cs_df_alt["Charging_Time"] = chargingtime
                point_list_df_alt = pd.DataFrame(point_list_alt_1, columns = ["Latitude", "Longitude"])
                cs_df = backend.get_nearest_point(point_list_df_alt, cs_df_alt)
                weather_df_alt = clustering.add_time_column(point_list_df_alt, cs_df_alt, f"{start_date} {start_time}")
                weather_df_alt = backend.get_weather(weather_df_alt)
                markers_alt = backend.get_severe_weather(weather_df_alt, markers_alt)
            
                return (
                    marker_lst,
                    markers,
                    mid_lat,
                    mid_lon,
                    point_list,
                    distance,
                    time,
                    initial_soc,
                    final_threshold,
                    start_time,
                    lst,
                    res,
                    last_leg,
                    night_travel,
                    time_end,
                    last_leg2,
                    rest_charge_last_leg,
                    
                    marker_lst_alt,
                    markers_alt,
                    mid_lat,
                    mid_lon,
                    point_list_alt_1,
                    distance_alt_1,
                    time_alt_1,
                    initial_soc,
                    final_threshold,
                    start_time,
                    lst_alt_1,
                    res_alt,
                    last_leg_alt,
                    night_travel_alt,
                    time_end_alt,
                    last_leg2_alt,
                    rest_charge_last_leg_alt)

        else:
            rest_charge_last_leg = []
            last_leg = [lst[keys[-1]]]
            idx_lst = [0]
            last_leg = dict(zip(idx_lst, last_leg))
            lst_coord = []
            lst2 = lst_coord
            marker_lst = []
            lst2.insert(0, [origin_lat, origin_lon])
            if len(intermediate_points_coords) > 0:
                for i in intermediate_points_coords:
                    lst2.append([i[1], i[2]])
            lst2.append([destination_lat, destination_lon])
            idx = [i for i in range(len(lst2))]
            res = {idx[i]: lst2[i] for i in range(len(idx))}
            point_list, distance, time = backend.get_route_many(lst2)
            marker_lst.append("L.marker([{latitude}, {longitude}])".format(latitude=origin_lat,\
                                                                                        longitude=origin_lon,
                                                                                                ))
            marker_lst.append("L.marker([{latitude}, {longitude}])".format(latitude=destination_lat,\
                                                                                        longitude=destination_lon,
                                                                                                ))  
            last_leg2 = []
            weather_df = clustering.add_time_column(point_list, f"{start_date} {start_time}")
            weather_df = backend.get_weather(weather_df)
            markers = backend.get_severe_weather(weather_df, markers)
           


            rest_charge_last_leg_alt = []
            last_leg_alt = [lst_alt_1[keys_alt[-1]]]
            idx_lst_alt = [0]
            last_leg_alt = dict(zip(idx_lst_alt, last_leg_alt))
            lst_coord_alt = []
            lst2_alt = lst_coord_alt
            marker_lst_alt = []
            lst2_alt.insert(0, [origin_lat, origin_lon])
            if len(intermediate_points_coords) > 0:
                for i in intermediate_points_coords:
                    lst2_alt.append([i[1], i[2]])
            lst2_alt.append([destination_lat, destination_lon])
            idx_alt = [i for i in range(len(lst2_alt))]
            res_alt = {idx_alt[i]: lst2_alt[i] for i in range(len(idx_alt))}
            point_list_alt_1, distance_alt_1, time_alt_1 = backend.get_route_many(lst2_alt)
            marker_lst_alt.append("L.marker([{latitude}, {longitude}])".format(latitude=origin_lat,\
                                                                                        longitude=origin_lon,
                                                                                                ))
            marker_lst_alt.append("L.marker([{latitude}, {longitude}])".format(latitude=destination_lat,\
                                                                                        longitude=destination_lon,
                                                                                                ))  
            last_leg2_alt = []

            weather_df_alt = clustering.add_time_column(point_list_alt_1, f"{start_date} {start_time}")
            weather_df_alt = backend.get_weather(weather_df_alt)
            markers_alt = backend.get_severe_weather(weather_df_alt, markers_alt)
                
            return (
                marker_lst,
                markers,
                mid_lat,
                mid_lon,
                point_list,
                distance,
                time,
                initial_soc,
                final_threshold,
                start_time,
                lst,
                res,
                last_leg,
                night_travel,
                time_end,
                last_leg2,
                rest_charge_last_leg,
                
                marker_lst_alt,
                markers_alt,
                mid_lat,
                mid_lon,
                point_list_alt_1,
                distance_alt_1,
                time_alt_1,
                initial_soc,
                final_threshold,
                start_time,
                lst_alt_1,
                res_alt,
                last_leg_alt,
                night_travel_alt,
                time_end_alt,
                last_leg2_alt,
                rest_charge_last_leg_alt)      

            
        


        
    
def process_inputs(
    start_point: str,
    end_point: str,
    range_start: float,
    range_arrival: int,
    start_time: str,
    start_date: str,
    intermediate_points: list,
    poi_radius: int,
    range_ev: float,
    bng_dat_path: str = "./resources/bng_df.csv",
):
    range_ev = float(range_ev) # Converting string input of range_ev to float
    origin = backend.get_coordinates(start_point) # Getting coordinates from address input, origin
    origin_lat, origin_lon = get_lat_long_from_coordinates(origin) # Getting latitude and longitude from address

    destination = backend.get_coordinates(end_point) # Getting coordinates from address input, destination
    destination_lat, destination_lon = get_lat_long_from_coordinates(destination) # Getting latitude and longitude from address

    intermediate_points_coords = [] # Empty list to store intermediate points 
    
    for i in range(len(intermediate_points)):  # For loop to get coordinates of intermediate points if there are any
        location = intermediate_points[i] # Accessing an intermediate point 
        coords = backend.get_coordinates(location) # Getting coordinates from address input, intermediate point
        intermediate_lat, intermediate_lon = get_lat_long_from_coordinates(coords) # Getting latitude and longitude from address
        intermediate_points_coords.append([i, intermediate_lat, intermediate_lon]) # Storing intermediate points in list
    
    # Creating markers list using origin and destination
    markers = get_markers(origin_lat, origin_lon, destination_lat, destination_lon)
      # Adding intermediate marker positions to marker list
    for i in intermediate_points_coords:
        markers = get_markers_intermediate(markers, i)

    # Computing mid lat and mid lon
    mid_lat, mid_lon = compute_midpoint(
        origin_lat, origin_lon, destination_lat, destination_lon
    )
 
    
    
    # If there are intermediate points, add to point list for query later
    if len(intermediate_points_coords) > 0:
        points = []
        for i in intermediate_points_coords:
            points.append([i[1],i[2]])
        points.insert(0, [origin_lat, origin_lon])
        points.append([destination_lat, destination_lon])
        points2 = copy.deepcopy(points)
        point_list, distance, time = backend.get_route_many(points) # Get route for origin, intermediate points and destination (Default)
        point_list_alt_1, distance_alt_1, time_alt_1 = backend.get_route_many_short(points2) # Get route for origin, intermediate points and destination (Short)

    else:

        # Get route for origin, and destination (Default)
        point_list, distance, time = backend.get_route(
            origin_lat, origin_lon, destination_lat, destination_lon
        )
        # Get route for origin, and destination (Short)
        point_list_alt_1, distance_alt_1, time_alt_1 = backend.get_route_short(
            origin_lat, origin_lon, destination_lat, destination_lon
        )
    
    
     # Getting stations that are near path    
    stations = get_stations_data(point_list, origin_lat, origin_lon, destination_lat, destination_lon, bng_dat_path)
    
    # If there are intermediate points, find the nearest charging stations to be shown on map
    if len(intermediate_points_coords) > 0:
        df_near = pd.DataFrame(columns = ["Station Name","Longitude","Latitude","Label"])
        for i in intermediate_points_coords:
            pt = [[i[1],i[2]]]
            df = clustering.near_points(pt, stations)
            df = df.drop_duplicates()
            df_near = pd.concat([df_near, df])
        
        #Adding markers of near charging stations to intermediate points
        for idx, row in df_near.iterrows():
            markers += "var {idd} = L.marker([{latitude}, {longitude}], markerOptions_CS);\
                                    {idd}.addTo(map);".format(
            idd=f"charging_near_intermediate_{idx+1}",
            latitude=row[2],
            longitude=row[1],
        )
            markers += """{idd}.bindPopup("{data}");""".format(idd=f"charging_near_intermediate_{idx+1}", data = f"Charging Point: {row[0]}")
    
    # Clustering data for path coordinates till destination (Default)
    df = get_clustering_data(point_list, origin_lat, origin_lon, destination_lat, destination_lon, stations, bng_dat_path)
    # Clustering data for path coordinates till destination (Short)
    df_alt_1 = get_clustering_data(point_list_alt_1, origin_lat, origin_lon, destination_lat, destination_lon,stations, bng_dat_path)

    # Defining variables required for battery script
    initial_soc = float(range_start)
    final_threshold = float(range_arrival)
    total_time = 0
    total_distance = distance
    min_threshold = 15
    dist_travelled = 0
    stop = 1
    range_needed = 0
    ave_speed = 40
    trip_start = start_time
    

    # Runing battery script for charge and go using default path
    lst = battery.station_coordinates(
        df,
        initial_soc,
        min_threshold,
        total_distance,
        dist_travelled,
        range_ev,
        stop,
        final_threshold,
        range_needed,
        ave_speed,
        start_time,
        trip_start,
        total_time,
    )
     # Runing battery script for charge and go using shorter path
    lst_alt_1 = battery.station_coordinates(
        df_alt_1,
        initial_soc,
        min_threshold,
        distance_alt_1,
        dist_travelled,
        range_ev,
        stop,
        final_threshold,
        range_needed,
        ave_speed,
        start_time,
        trip_start,
        total_time,
    )

    # If the trip is incomplete, meaning not enough charging stations, print message and return None
    if lst == "Trip cannot be completed as no charging station is available in the vicinity":
        return None
     # If the trip can be completed with no charging, it falls under this case since there are no coordinates inserted from script
    if type(lst) == str:
         #Data processing of dictionary from battery script to individual variables to be rendered in HTML later
        night_travel = False
        time_end = 0

        if len(intermediate_points_coords) < 1:
            point_list, distance, time = backend.get_route(origin_lat, origin_lon, destination_lat, destination_lon)
        
        else:
            point_list, distance, time = backend.get_route_many(points)
        

        lst = [lst]
        idx_lst = [0]
        lst = dict(zip(idx_lst, lst))
                
        lst_coord = []
        lst2 = lst_coord
        marker_lst = []
        lst2.insert(0, [origin_lat, origin_lon])
        lst2.append([destination_lat, destination_lon])
        idx = [i for i in range(len(lst2))]
        res = {idx[i]: lst2[i] for i in range(len(idx))}
        last_leg = {0: [initial_soc, distance, initial_soc - (distance/ (range_ev/100))]}


        marker_lst.append("L.marker([{latitude}, {longitude}])".format(latitude=origin_lat,\
                                                                                        longitude=origin_lon,
                                                                                                ))
        marker_lst.append("L.marker([{latitude}, {longitude}])".format(latitude=destination_lat,\
                                                                                        longitude=destination_lon,
                                                                                                ))
        weather_df = clustering.add_time_column(point_list, f"{start_date} {start_time}")
        weather_df = backend.get_weather(weather_df)
        markers = backend.get_severe_weather(weather_df, markers)
           


        night_travel_alt = False
        time_end_alt = 0
        if len(intermediate_points_coords) < 1:
            point_list_alt_1, distance_alt_1, time_alt_1 = backend.get_route_short(origin_lat, origin_lon, destination_lat, destination_lon)
        else:
            point_list_alt_1, distance_alt_1, time_alt_1 = backend.get_route_many_short(points)
        



        lst_alt_1 = [lst_alt_1]
        idx_lst_alt = [0]
        lst_alt_1 = dict(zip(idx_lst_alt, lst_alt_1))
                
        lst_coord_alt = []
        lst2_alt = lst_coord_alt
        marker_lst_alt = []
        lst2_alt.insert(0, [origin_lat, origin_lon])
        lst2_alt.append([destination_lat, destination_lon])
        idx_alt = [i for i in range(len(lst2_alt))]
        res_alt = {idx_alt[i]: lst2_alt[i] for i in range(len(idx_alt))}
        last_leg_alt = {0: [initial_soc, distance, initial_soc - (distance/ (range_ev/100))]}


        marker_lst_alt.append("L.marker([{latitude}, {longitude}])".format(latitude=origin_lat,\
                                                                                        longitude=origin_lon,
                                                                                                ))
        marker_lst_alt.append("L.marker([{latitude}, {longitude}])".format(latitude=destination_lat,\
                                                                                        longitude=destination_lon,
                                                                                                ))

        markers_alt = markers  
        weather_df_alt = clustering.add_time_column(point_list_alt_1, f"{start_date} {start_time}")
        weather_df_alt = backend.get_weather(weather_df_alt)
        markers_alt = backend.get_severe_weather(weather_df_alt, markers_alt)
                                                               
                               
        return (
        marker_lst,
        markers,
        mid_lat,
        mid_lon,
        point_list,
        distance,
        time,
        initial_soc,
        final_threshold,
        start_time,
        lst,
        res,
        last_leg,
        night_travel,
        time_end,
        
        marker_lst_alt,
                    markers_alt,
                    mid_lat,
                    mid_lon,
                    point_list_alt_1,
                    distance_alt_1,
                    time_alt_1,
                    initial_soc,
                    final_threshold,
                    start_time,
                    lst_alt_1,
                    res_alt,
                    last_leg_alt,
                    night_travel_alt,
                    time_end_alt)

    else:
         #Data processing of dictionary from battery script to individual variables to be rendered in HTML later
        keys = list(lst.keys())
        time_end = lst[keys[-1]][0]
        night_travel = lst[keys[-1]][1]
        if len(keys) > 1:
            last_leg = [lst[keys[-2]]]
            idx_lst = [0]
            last_leg = dict(zip(idx_lst, last_leg))

            lst3 = copy.deepcopy(lst)

            del lst[keys[-1]]
            keys = keys[:-1]
            del lst[keys[-1]]
            marker_lst = []
            lst_coord = []
            
            for i in lst.keys():
                id = "stop" + str(i)
                markers += "var {idd} = L.marker([{latitude}, {longitude}], markerOptions_CS);\
                                                {idd}.addTo(map);".format(idd=id, latitude=float(lst[i][2]),\
                                                                                        longitude=float(lst[i][3]),
                                                                                                )

                marker_lst.append("L.marker([{latitude}, {longitude}])".format(latitude=float(lst[i][2]),\
                                                                                        longitude=float(lst[i][3]),
                                                                                                )
                                )
                lst_coord.append([lst[i][2],lst[i][3]])
  

            
            

            df = pd.DataFrame(columns = ["Name","Category","Latitude", "Longitude"])
            


            for i in lst_coord:
                df2 = backend.get_POI(i[0], i[1], poi_radius)
                df = pd.concat([df, df2],ignore_index=True)
            
            for index, row in df.iterrows():
                id = "POI" + str(index)
                
                
                markers += "var {idd} = L.marker([{latitude}, {longitude}], markerOptions_POI);\
                                                {idd}.addTo(map);".format(idd=id, latitude=float(row[2]),\
                                                                                        longitude=float(row[3]),
                                                                                        name = row[0],
                                                                                        category = row[1] )
                
                data = f"{row[0]}, {row[1]}"                                                                        
                markers += """{idd}.bindPopup("{data}");""".format(idd=id, data = data)

                marker_lst.append("L.marker([{latitude}, {longitude}])".format(latitude=float(row[2]),\
                                                                                        longitude=float(row[3]),
                                                                                               ))
            
       

            lst2 = lst_coord
            cs = copy.deepcopy(lst2)
            lst2.insert(0, [origin_lat, origin_lon])
            if len(intermediate_points_coords) > 0:
                for i in intermediate_points_coords:
                    lst2.append([i[1], i[2]])
            lst2.append([destination_lat, destination_lon])
            idx = [i for i in range(len(lst2))]
            res = {idx[i]: lst2[i] for i in range(len(idx))}
           
            point_list, distance, time = backend.get_route_many(lst2)
            
            
            chargingtime = []
            for i in range(1, len(lst)+1):
                chargingtime.append(lst[i][5])
            cs_df = pd.DataFrame(cs, columns = ["Latitude", "Longitude"])
            cs_df["Charging_Time"] = chargingtime
            point_list_df = pd.DataFrame(point_list, columns = ["Latitude", "Longitude"])
            cs_df = backend.get_nearest_point(point_list_df, cs_df)
            weather_df = clustering.add_time_column(point_list_df, cs_df, f"{start_date} {start_time}")
            weather_df = backend.get_weather(weather_df)
            markers = backend.get_severe_weather(weather_df, markers)
            # For alternate route 1
        
            keys_alt = list(lst_alt_1.keys())
            time_end_alt = lst_alt_1[keys_alt[-1]][0]
            night_travel_alt = lst_alt_1[keys_alt[-1]][1]
            if len(keys_alt) > 1:
                last_leg_alt = [lst_alt_1[keys_alt[-2]]]
                idx_lst_alt = [0]
                last_leg_alt = dict(zip(idx_lst_alt, last_leg_alt))

                lst3_alt = copy.deepcopy(lst_alt_1)

                del lst_alt_1[keys_alt[-1]]
                keys_alt = keys_alt[:-1]
                del lst_alt_1[keys_alt[-1]]
                marker_lst_alt = []
                lst_coord_alt = []
                markers_alt = markers

                for i in lst_alt_1.keys():
                    id_alt = "stop" + str(i)
                    markers_alt += "var {idd} = L.marker([{latitude}, {longitude}], markerOptions_CS);\
                                                    {idd}.addTo(map);".format(idd=id_alt, latitude=float(lst_alt_1[i][2]),\
                                                                                            longitude=float(lst_alt_1[i][3]),
                                                                                                    )

                    marker_lst_alt.append("L.marker([{latitude}, {longitude}])".format(latitude=float(lst_alt_1[i][2]),\
                                                                                            longitude=float(lst_alt_1[i][3]),
                                                                                                    )
                                    )
                    lst_coord_alt.append([lst_alt_1[i][2],lst_alt_1[i][3]])

                

                df_alt = pd.DataFrame(columns = ["Name","Category","Latitude", "Longitude"])
                for i in lst_coord_alt:
                    df2 = backend.get_POI(i[0], i[1], poi_radius)
                    df_alt = pd.concat([df_alt, df2],ignore_index=True)
                
                for index, row in df_alt.iterrows():
                    id_alt = "POI_alt" + str(index)
                    
                    
                    markers_alt += "var {idd} = L.marker([{latitude}, {longitude}],markerOptions_POI);\
                                                    {idd}.addTo(map);".format(idd=id_alt, latitude=float(row[2]),\
                                                                                            longitude=float(row[3]),
                                                                                            name = row[0],
                                                                                            category = row[1] )
                    
                    data = f"{row[0]}, {row[1]}"                                                                        
                    markers_alt += """{idd}.bindPopup("{data}");""".format(idd=id_alt, data = data)

                    marker_lst_alt.append("L.marker([{latitude}, {longitude}])".format(latitude=float(row[2]),\
                                                                                            longitude=float(row[3]),
                                                                                                    ))
                

                lst2_alt = lst_coord_alt
                cs_alt = copy.deepcopy(lst2_alt)
                lst2_alt.insert(0, [origin_lat, origin_lon])
                if len(intermediate_points_coords) > 0:
                    for i in intermediate_points_coords:
                        lst2_alt.append([i[1], i[2]])
                lst2_alt.append([destination_lat, destination_lon])
                idx_alt = [i for i in range(len(lst2_alt))]
                res_alt = {idx_alt[i]: lst2_alt[i] for i in range(len(idx_alt))}
                point_list_alt_1, distance_alt_1, time_alt_1 = backend.get_route_many_short(lst2_alt)

                chargingtime = []
                for i in range(1, len(lst)+1):
                    chargingtime.append(lst[i][5])
                cs_df_alt = pd.DataFrame(cs_alt, columns = ["Latitude", "Longitude"])
                cs_df_alt["Charging_Time"] = chargingtime
                point_list_df_alt = pd.DataFrame(point_list_alt_1, columns = ["Latitude", "Longitude"])
                cs_df = backend.get_nearest_point(point_list_df_alt, cs_df_alt)
                weather_df_alt = clustering.add_time_column(point_list_df_alt, cs_df_alt, f"{start_date} {start_time}")
                weather_df_alt = backend.get_weather(weather_df_alt)
                markers_alt = backend.get_severe_weather(weather_df_alt, markers_alt)
            

                
                return (
                    marker_lst,
                    markers,
                    mid_lat,
                    mid_lon,
                    point_list,
                    distance,
                    time,
                    initial_soc,
                    final_threshold,
                    start_time,
                    lst,
                    res,
                    last_leg,
                    night_travel,
                    time_end,
                    
                    marker_lst_alt,
                    markers_alt,
                    mid_lat,
                    mid_lon,
                    point_list_alt_1,
                    distance_alt_1,
                    time_alt_1,
                    initial_soc,
                    final_threshold,
                    start_time,
                    lst_alt_1,
                    res_alt,
                    last_leg_alt,
                    night_travel_alt,
                    time_end_alt)

        else:
            last_leg = [lst[keys[-1]]]
            idx_lst = [0]
            last_leg = dict(zip(idx_lst, last_leg))
            lst_coord = []
            lst2 = lst_coord
            cs = copy.deepcopy(lst2)
            marker_lst = []
            lst2.insert(0, [origin_lat, origin_lon])
            if len(intermediate_points_coords) > 0:
                    for i in intermediate_points_coords:
                        lst2.append([i[1], i[2]])
            lst2.append([destination_lat, destination_lon])
            idx = [i for i in range(len(lst2))]
            res = {idx[i]: lst2[i] for i in range(len(idx))}
            point_list, distance, time = backend.get_route_many(lst2)
            marker_lst.append("L.marker([{latitude}, {longitude}])".format(latitude=origin_lat,\
                                                                                        longitude=origin_lon,
                                                                                                ))
            marker_lst.append("L.marker([{latitude}, {longitude}])".format(latitude=destination_lat,\
                                                                                        longitude=destination_lon,
                                                                                                ))  

            
            chargingtime = []
            for i in range(1, len(lst)+1):
                chargingtime.append(lst[i][5])
            cs_df = pd.DataFrame(cs, columns = ["Latitude", "Longitude"])
            cs_df["Charging_Time"] = chargingtime
            point_list_df = pd.DataFrame(point_list, columns = ["Latitude", "Longitude"])
            cs_df = backend.get_nearest_point(point_list_df, cs_df)
            weather_df = clustering.add_time_column(point_list_df, cs_df, f"{start_date} {start_time}")
            weather_df = backend.get_weather(weather_df)
            markers = backend.get_severe_weather(weather_df, markers)

            
            last_leg_alt = [lst_alt_1[keys_alt[-1]]]
            idx_lst_alt = [0]
            last_leg_alt = dict(zip(idx_lst_alt, last_leg_alt))
            lst_coord_alt = []
            lst2_alt = lst_coord_alt
            cs_alt = copy.deepcopy(lst2_alt)
            marker_lst_alt = []
            lst2_alt.insert(0, [origin_lat, origin_lon])
            if len(intermediate_points_coords) > 0:
                    for i in intermediate_points_coords:
                        lst2_alt.append([i[1], i[2]])
            lst2_alt.append([destination_lat, destination_lon])
            idx_alt = [i for i in range(len(lst2_alt))]
            res_alt = {idx_alt[i]: lst2_alt[i] for i in range(len(idx_alt))}
            point_list_alt_1, distance_alt_1, time_alt_1 = backend.get_route_many_short(lst2_alt)
            marker_lst_alt.append("L.marker([{latitude}, {longitude}])".format(latitude=origin_lat,\
                                                                                        longitude=origin_lon,
                                                                                                ))
            marker_lst_alt.append("L.marker([{latitude}, {longitude}])".format(latitude=destination_lat,\
                                                                                        longitude=destination_lon,
                                                                                                ))  
                                                                      
            chargingtime = []
            for i in range(1, len(lst)+1):
                chargingtime.append(lst[i][5])
            cs_df_alt = pd.DataFrame(cs_alt, columns = ["Latitude", "Longitude"])
            cs_df_alt["Charging_Time"] = chargingtime
            point_list_df_alt = pd.DataFrame(point_list_alt_1, columns = ["Latitude", "Longitude"])
            cs_df = backend.get_nearest_point(point_list_df_alt, cs_df_alt)
            weather_df_alt = clustering.add_time_column(point_list_df_alt, cs_df_alt, f"{start_date} {start_time}")
            weather_df_alt = backend.get_weather(weather_df_alt)
            markers_alt = backend.get_severe_weather(weather_df_alt, markers_alt)
            
                
            return (
                marker_lst,
                markers,
                mid_lat,
                mid_lon,
                point_list,
                distance,
                time,
                initial_soc,
                final_threshold,
                start_time,
                lst,
                res,
                last_leg,
                night_travel,
                time_end,
                
                    marker_lst_alt,
                    markers_alt,
                    mid_lat,
                    mid_lon,
                    point_list_alt_1,
                    distance_alt_1,
                    time_alt_1,
                    initial_soc,
                    final_threshold,
                    start_time,
                    lst_alt_1,
                    res_alt,
                    last_leg_alt,
                    night_travel_alt,
                    time_end_alt 
                )      
    

def process_inputs_nonight(
    start_point: str,
    end_point: str,
    range_start: float,
    range_arrival: int,
    start_time: str,
    start_date: str,
    intermediate_points: list,
    poi_radius: int,
    range_ev: float,
    bng_dat_path: str = "./resources/bng_df.csv",
):  
    range_ev = float(range_ev) # Converting string input of range_ev to float
    origin = backend.get_coordinates(start_point) # Getting coordinates from address input, origin
    origin_lat, origin_lon = get_lat_long_from_coordinates(origin) # Getting latitude and longitude from address


    destination = backend.get_coordinates(end_point) # Getting coordinates from address input, destination
    destination_lat, destination_lon = get_lat_long_from_coordinates(destination) # Getting latitude and longitude from address


    intermediate_points_coords = [] # Empty list to store intermediate points 
    
    for i in range(len(intermediate_points)): # For loop to get coordinates of intermediate points if there are any
        location = intermediate_points[i] # Accessing an intermediate point 
        coords = backend.get_coordinates(location) # Getting coordinates from address input, intermediate point
        intermediate_lat, intermediate_lon = get_lat_long_from_coordinates(coords) # Getting latitude and longitude from address
        intermediate_points_coords.append([i, intermediate_lat, intermediate_lon]) # Storing intermediate points in list
    

    # Creating markers list using origin and destination
    markers = get_markers(origin_lat, origin_lon, destination_lat, destination_lon)
    # Adding intermediate marker positions to marker list
    for i in intermediate_points_coords:
        markers = get_markers_intermediate(markers, i)

    # Computing mid lat and mid lon
    mid_lat, mid_lon = compute_midpoint(
        origin_lat, origin_lon, destination_lat, destination_lon
    )
    # If there are intermediate points, add to point list for query later
    if len(intermediate_points_coords) > 0:
        points = []
        for i in intermediate_points_coords:
            points.append([i[1],i[2]])
        points.insert(0, [origin_lat, origin_lon])
        points.append([destination_lat, destination_lon])
        points2 = copy.deepcopy(points)
        point_list, distance, time = backend.get_route_many(points)
        point_list_alt_1, distance_alt_1, time_alt_1 = backend.get_route_many_short(points2)

    else:
        # Get route for origin, and destination (Default)
        point_list, distance, time = backend.get_route(
            origin_lat, origin_lon, destination_lat, destination_lon
        )
        # Get route for origin, and destination (Short)
        point_list_alt_1, distance_alt_1, time_alt_1 = backend.get_route_short(
            origin_lat, origin_lon, destination_lat, destination_lon
        )
    
    # Getting stations that are near path   
    stations = get_stations_data(point_list, origin_lat, origin_lon, destination_lat, destination_lon, bng_dat_path)
    
     # If there are intermediate points, find the nearest charging stations to be shown on map
    if len(intermediate_points_coords) > 0:
        df_near = pd.DataFrame(columns = ["Station Name","Longitude","Latitude","Label"])
        for i in intermediate_points_coords:
            pt = [[i[1],i[2]]]
            df = clustering.near_points(pt, stations)
            df = df.drop_duplicates()
            df_near = pd.concat([df_near, df])

         #Adding markers of near charging stations to intermediate points 
        for idx, row in df_near.iterrows():
            markers += "var {idd} = L.marker([{latitude}, {longitude}], markerOptions_CS);\
                                    {idd}.addTo(map);".format(
            idd=f"charging_near_intermediate_{idx+1}",
            latitude=row[2],
            longitude=row[1],
        )
            markers += """{idd}.bindPopup("{data}");""".format(idd=f"charging_near_intermediate_{idx+1}", data = f"Charging Point: {row[0]}")
    
    
     # Clustering data for path coordinates till destination (Default)
    df = get_clustering_data(point_list,origin_lat, origin_lon, destination_lat, destination_lon, stations, bng_dat_path)
     # Clustering data for path coordinates till destination (Short)
    df_alt_1 = get_clustering_data(point_list_alt_1, origin_lat, origin_lon, destination_lat, destination_lon,stations, bng_dat_path)
    

    # Defining variables required for battery script
    initial_soc = float(range_start)
    final_threshold = float(range_arrival)
    total_time = 0
    total_distance = distance
    min_threshold = 15
    dist_travelled = 0

    stop = 1
    range_needed = 0
    ave_speed = 40
    trip_start = start_time

    # Runing battery script for charge and go using default path
    lst = battery.station_coordinates_no_night(
        df,
        initial_soc,
        min_threshold,
        total_distance,
        dist_travelled,
        range_ev,
        stop,
        final_threshold,
        range_needed,
        ave_speed,
        start_time,
        trip_start,
        total_time,
    )
    # Runing battery script for charge and go using shorter path
    lst_alt_1 = battery.station_coordinates_no_night(
        df_alt_1,
        initial_soc,
        min_threshold,
        distance_alt_1,
        dist_travelled,
        range_ev,
        stop,
        final_threshold,
        range_needed,
        ave_speed,
        start_time,
        trip_start,
        total_time,
    )

    # If the trip is incomplete, meaning not enough charging stations, print message and return None
    if lst == "Trip cannot be completed as no charging station is available in the vicinity":
        return None

    # If the trip can be completed with no charging, it falls under this case since there are no coordinates inserted from script
    if type(lst) == str:
        #Data processing of dictionary from battery script to individual variables to be rendered in HTML later
        night_travel = False
        time_end = 0

        if len(intermediate_points_coords) < 1:
            point_list, distance, time = backend.get_route(origin_lat, origin_lon, destination_lat, destination_lon)
        
        else:
            point_list, distance, time = backend.get_route_many(points)
        



        lst = [lst]
        idx_lst = [0]
        lst = dict(zip(idx_lst, lst))
                
        lst_coord = []
        lst2 = lst_coord
        marker_lst = []
        lst2.insert(0, [origin_lat, origin_lon])
        lst2.append([destination_lat, destination_lon])
        idx = [i for i in range(len(lst2))]
        res = {idx[i]: lst2[i] for i in range(len(idx))}
        last_leg = {0: [initial_soc, distance, initial_soc - (distance/ (range_ev/100))]}


        marker_lst.append("L.marker([{latitude}, {longitude}])".format(latitude=origin_lat,\
                                                                                        longitude=origin_lon,
                                                                                                ))
        marker_lst.append("L.marker([{latitude}, {longitude}])".format(latitude=destination_lat,\
                                                                                        longitude=origin_lon,
                                                                                                ))
        
        weather_df = clustering.add_time_column(point_list, f"{start_date} {start_time}")
        weather_df = backend.get_weather(weather_df)
        markers = backend.get_severe_weather(weather_df, markers)
           
        
        night_travel_alt = False
        time_end_alt = 0

        if len(intermediate_points_coords) < 1:
            point_list_alt_1, distance_alt_1, time_alt_1 = backend.get_route_short(origin_lat, origin_lon, destination_lat, destination_lon)
        
        else:
            point_list_alt_1, distance_alt_1, time_alt_1 = backend.get_route_many_short(points)
        
            

        lst_alt_1 = [lst_alt_1]
        idx_lst_alt = [0]
        lst = dict(zip(idx_lst_alt, lst_alt_1))
                
        lst_coord_alt = []
        lst2_alt = lst_coord_alt
        marker_lst_alt = []
        lst2_alt.insert(0, [origin_lat, origin_lon])
        lst2_alt.append([destination_lat, destination_lon])
        idx_alt = [i for i in range(len(lst2_alt))]
        
        res_alt = {idx_alt[i]: lst2_alt[i] for i in range(len(idx_alt))}
        last_leg_alt = {0: [initial_soc, distance, initial_soc - (distance/ (range_ev/100))]}

        marker_lst_alt.append("L.marker([{latitude}, {longitude}])".format(latitude=origin_lat,\
                                                                                        longitude=origin_lon,
                                                                                                ))
        marker_lst_alt.append("L.marker([{latitude}, {longitude}])".format(latitude=destination_lat,\
                                                                     longitude=destination_lon, markers_alt = markers    
                                                                                             ))

        weather_df_alt = clustering.add_time_column(point_list_alt_1, f"{start_date} {start_time}")
        weather_df_alt = backend.get_weather(weather_df_alt)
        markers_alt = backend.get_severe_weather(weather_df_alt, markers_alt)
                    
        return (
        marker_lst,
        markers,
        mid_lat,
        mid_lon,
        point_list,
        distance,
        time,
        initial_soc,
        final_threshold,
        start_time,
        lst,
        res,
        last_leg,
        night_travel,
        time_end,
        
        marker_lst_alt,
        markers_alt,
        mid_lat,
                mid_lon,
                    point_list_alt_1,
                    distance_alt_1,
                    time_alt_1,
                    initial_soc,
                    final_threshold,
                    start_time,
                    lst_alt_1,
                    res_alt,
                    last_leg_alt,
                    night_travel_alt,
                    time_end_alt)

    else:
         #Data processing of dictionary from battery script to individual variables to be rendered in HTML later
        keys = list(lst.keys())
        time_end = lst[keys[-1]][0]
        night_travel = lst[keys[-1]][1]
        if len(keys) > 1:
            last_leg = [lst[keys[-2]]]
            idx_lst = [0]
            last_leg = dict(zip(idx_lst, last_leg))

            lst3 = copy.deepcopy(lst)

            del lst[keys[-1]]
            keys = keys[:-1]
            del lst[keys[-1]]
            marker_lst = []
            lst_coord = []

            for i in lst.keys():
                id = "stop" + str(i)
                markers += "var {idd} = L.marker([{latitude}, {longitude}], markerOptions_CS);\
                                                {idd}.addTo(map);".format(idd=id, latitude=float(lst[i][2]),\
                                                                                        longitude=float(lst[i][3]),
                                                                                                )

                marker_lst.append("L.marker([{latitude}, {longitude}])".format(latitude=float(lst[i][2]),\
                                                                                        longitude=float(lst[i][3]),
                                                                                                )
                                )
                lst_coord.append([lst[i][2],lst[i][3]])

            
            df = pd.DataFrame(columns = ["Name","Category","Latitude", "Longitude"])
            for i in lst_coord:
                df2 = backend.get_Hotel(i[0], i[1])
                df3 = backend.get_POI(i[0], i[1], poi_radius)

                df = pd.concat([df, df2, df3],ignore_index=True)
            
            for index, row in df.iterrows():
                if row[1] != "accommodation":
                    id = "Hotel" + str(index)

                    markers += "var {idd} = L.marker([{latitude}, {longitude}], markerOptions_POI);\
                                                    {idd}.addTo(map);".format(idd=id, latitude=float(row[2]),\
                                                                                            longitude=float(row[3]),
                                                                                            name = row[0],
                                                                                            category = row[1] )
                    
                    data = f"{row[0]}, {row[1]}"                                                                        
                    markers += """{idd}.bindPopup("{data}");""".format(idd=id, data = data)

                    marker_lst.append("L.marker([{latitude}, {longitude}])".format(latitude=float(row[2]),\
                                                                                            longitude=float(row[3]),
                                                                                                    ))

                else:
                    id = "POI" + str(index)
            
                    markers += "var {idd} = L.marker([{latitude}, {longitude}], markerOptions_Hotel);\
                                                    {idd}.addTo(map);".format(idd=id, latitude=float(row[2]),\
                                                                                            longitude=float(row[3]),
                                                                                            name = row[0],
                                                                                            category = row[1] )
                    
                    data = f"{row[0]}, {row[1]}"                                                                        
                    markers += """{idd}.bindPopup("{data}");""".format(idd=id, data = data)

                    marker_lst.append("L.marker([{latitude}, {longitude}])".format(latitude=float(row[2]),\
                                                                                            longitude=float(row[3]),
                                                                                                    ))                                                                     
                
            
            lst2 = lst_coord
            cs = copy.deepcopy(lst2)
            lst2.insert(0, [origin_lat, origin_lon])
            if len(intermediate_points_coords) > 0:
                for i in intermediate_points_coords:
                    lst2.append([i[1], i[2]])
            lst2.append([destination_lat, destination_lon])
            idx = [i for i in range(len(lst2))]
            res = {idx[i]: lst2[i] for i in range(len(idx))}
            point_list, distance, time = backend.get_route_many(lst2)
            chargingtime = []
            for i in range(1, len(lst)+1):
                chargingtime.append(lst[i][5])
            cs_df = pd.DataFrame(cs, columns = ["Latitude", "Longitude"])
            cs_df["Charging_Time"] = chargingtime
            point_list_df = pd.DataFrame(point_list, columns = ["Latitude", "Longitude"])
            cs_df = backend.get_nearest_point(point_list_df, cs_df)
            weather_df = clustering.add_time_column(point_list_df, cs_df, f"{start_date} {start_time}")
            weather_df = backend.get_weather(weather_df)
            markers = backend.get_severe_weather(weather_df, markers)


            # For alternate route 1
            keys_alt = list(lst_alt_1.keys())
            time_end_alt = lst_alt_1[keys_alt[-1]][0]
            night_travel_alt = lst_alt_1[keys_alt[-1]][1]
            if len(keys_alt) > 1:
                last_leg_alt = [lst_alt_1[keys_alt[-2]]]
                idx_lst_alt = [0]
                last_leg_alt = dict(zip(idx_lst_alt, last_leg_alt))

                lst3_alt = copy.deepcopy(lst_alt_1)

                del lst_alt_1[keys_alt[-1]]
                keys_alt = keys_alt[:-1]
                del lst_alt_1[keys_alt[-1]]
                marker_lst_alt = []
                lst_coord_alt = []
                markers_alt = markers

                for i in lst_alt_1.keys():
                    id_alt = "stop" + str(i)
                    markers_alt += "var {idd} = L.marker([{latitude}, {longitude}], markerOptions_CS);\
                                                    {idd}.addTo(map);".format(idd=id_alt, latitude=float(lst_alt_1[i][2]),\
                                                                                            longitude=float(lst_alt_1[i][3]),
                                                                                                    )

                    marker_lst_alt.append("L.marker([{latitude}, {longitude}])".format(latitude=float(lst_alt_1[i][2]),\
                                                                                            longitude=float(lst_alt_1[i][3]),
                                                                                                    )
                                    )
                    lst_coord_alt.append([lst_alt_1[i][2],lst_alt_1[i][3]])

            df_alt = pd.DataFrame(columns = ["Name","Category","Latitude", "Longitude"])
            for i in lst_coord_alt:
                df2 = backend.get_Hotel(i[0], i[1])
                df3 = backend.get_POI(i[0], i[1], poi_radius)
                df_alt = pd.concat([df_alt, df2 ,df3],ignore_index=True)
                
            for index, row in df_alt.iterrows():
                if row[1] != "accommodation":
                    id = "Hotel" + str(index)

                    markers_alt += "var {idd} = L.marker([{latitude}, {longitude}], markerOptions_POI);\
                                                                {idd}.addTo(map);".format(idd=id, latitude=float(row[2]),\
                                                                                                        longitude=float(row[3]),
                                                                                                        name = row[0],
                                                                                                        category = row[1] )
                                
                    data = f"{row[0]}, {row[1]}"                                                                        
                    markers_alt += """{idd}.bindPopup("{data}");""".format(idd=id, data = data)

                    marker_lst_alt.append("L.marker([{latitude}, {longitude}])".format(latitude=float(row[2]),\
                                                                                                        longitude=float(row[3]),
                                                                                                                ))

                else:
                    id = "POI" + str(index)
                        
                    markers_alt += "var {idd} = L.marker([{latitude}, {longitude}], markerOptions_Hotel);\
                                                                {idd}.addTo(map);".format(idd=id, latitude=float(row[2]),\
                                                                                                        longitude=float(row[3]),
                                                                                                        name = row[0],
                                                                                                        category = row[1] )
                                
                    data = f"{row[0]}, {row[1]}"                                                                        
                    markers_alt += """{idd}.bindPopup("{data}");""".format(idd=id, data = data)

                    marker_lst_alt.append("L.marker([{latitude}, {longitude}])".format(latitude=float(row[2]),\
                                                                                                        longitude=float(row[3]),
                                                                                                                ))                                                                     
                
            lst2_alt = lst_coord_alt
            cs_alt = copy.deepcopy(lst2_alt)
            lst2_alt.insert(0, [origin_lat, origin_lon])
            if len(intermediate_points_coords) > 0:
                    for i in intermediate_points_coords:
                        lst2_alt.append([i[1], i[2]])
            lst2_alt.append([destination_lat, destination_lon])
            idx_alt = [i for i in range(len(lst2_alt))]

            res_alt = {idx_alt[i]: lst2_alt[i] for i in range(len(idx_alt))}
            point_list_alt_1, distance_alt_1, time_alt_1 = backend.get_route_many_short(lst2_alt)
            chargingtime = []
            for i in range(1, len(lst)+1):
                chargingtime.append(lst[i][5])
            cs_df_alt = pd.DataFrame(cs_alt, columns = ["Latitude", "Longitude"])
            cs_df_alt["Charging_Time"] = chargingtime
            point_list_df_alt = pd.DataFrame(point_list_alt_1, columns = ["Latitude", "Longitude"])
            cs_df = backend.get_nearest_point(point_list_df_alt, cs_df_alt)
            weather_df_alt = clustering.add_time_column(point_list_df_alt, cs_df_alt, f"{start_date} {start_time}")
            weather_df_alt = backend.get_weather(weather_df_alt)
            markers_alt = backend.get_severe_weather(weather_df_alt, markers_alt)


            return (
                marker_lst,
                markers,
                mid_lat,
                mid_lon,
                point_list,
                distance,
                time,
                initial_soc,
                final_threshold,
                start_time,
                lst,
                res,
                last_leg,
                night_travel,
                time_end,
                
                marker_lst_alt,
                    markers_alt,
                    mid_lat,
                    mid_lon,
                    point_list_alt_1,
                    distance_alt_1,
                    time_alt_1,
                    initial_soc,
                    final_threshold,
                    start_time,
                    lst_alt_1,
                    res_alt,
                    last_leg_alt,
                    night_travel_alt,
                    time_end_alt)

        else:
            last_leg = [lst[keys[-1]]]
            idx_lst = [0]
            last_leg = dict(zip(idx_lst, last_leg))
            lst_coord = []
            lst2 = lst_coord
            cs = copy.deepcopy(lst2)
            marker_lst = []
            lst2.insert(0, [origin_lat, origin_lon])
            if len(intermediate_points_coords) > 0:
                    for i in intermediate_points_coords:
                        lst2.append([i[1], i[2]])
            lst2.append([destination_lat, destination_lon])
            idx = [i for i in range(len(lst2))]
            res = {idx[i]: lst2[i] for i in range(len(idx))}
            point_list, distance, time = backend.get_route_many(lst2)
            marker_lst.append("L.marker([{latitude}, {longitude}])".format(latitude=origin_lat,\
                                                                                        longitude=origin_lon,
                                                                                                ))
            marker_lst.append("L.marker([{latitude}, {longitude}])".format(latitude=destination_lat,\
                                                                        longitude=destination_lon,
                                                                                                ))  


            chargingtime = []
            for i in range(1, len(lst)+1):
                chargingtime.append(lst[i][5])
            cs_df = pd.DataFrame(cs, columns = ["Latitude", "Longitude"])
            cs_df["Charging_Time"] = chargingtime
            point_list_df = pd.DataFrame(point_list, columns = ["Latitude", "Longitude"])
            cs_df = backend.get_nearest_point(point_list_df, cs_df)
            weather_df = clustering.add_time_column(point_list_df, cs_df, f"{start_date} {start_time}")
            weather_df = backend.get_weather(weather_df)
            markers = backend.get_severe_weather(weather_df, markers)
                                                                                        
            last_leg_alt = [lst_alt_1[keys_alt[-1]]]
            idx_lst_alt = [0]
            last_leg_alt = dict(zip(idx_lst_alt, last_leg_alt))
            lst_coord_alt = []
            lst2_alt = lst_coord_alt
            cs_alt = copy.deepcopy(lst2_alt)
            marker_lst_alt = []
            lst2_alt.insert(0, [origin_lat, origin_lon])
            if len(intermediate_points_coords) > 0:
                    for i in intermediate_points_coords:
                        lst2_alt.append([i[1], i[2]])
            lst2_alt.append([destination_lat, destination_lon])
            idx_alt = [i for i in range(len(lst2_alt))]
            res_alt = {idx_alt[i]: lst2_alt[i] for i in range(len(idx_alt))}
            point_list_alt_1, distance_alt_1, time_alt_1 = backend.get_route_many_short(lst2_alt)
            marker_lst_alt.append("L.marker([{latitude}, {longitude}])".format(latitude=origin_lat,\
                                                                                        longitude=origin_lon,
                                                                                                ))
            marker_lst_alt.append("L.marker([{latitude}, {longitude}])".format(latitude=destination_lat,\
                                                                                        longitude=destination_lon,
            
                                                                                                    ))  
                                                                      
            chargingtime = []
            for i in range(1, len(lst)+1):
                chargingtime.append(lst[i][5])
            cs_df_alt = pd.DataFrame(cs_alt, columns = ["Latitude", "Longitude"])
            cs_df_alt["Charging_Time"] = chargingtime
            point_list_df_alt = pd.DataFrame(point_list_alt_1, columns = ["Latitude", "Longitude"])
            cs_df = backend.get_nearest_point(point_list_df_alt, cs_df_alt)
            weather_df_alt = clustering.add_time_column(point_list_df_alt, cs_df_alt, f"{start_date} {start_time}")
            weather_df_alt = backend.get_weather(weather_df_alt)
            markers_alt = backend.get_severe_weather(weather_df_alt, markers_alt)
            

            return (
                marker_lst,
                markers,
                mid_lat,
                mid_lon,
                point_list,
                distance,
                time,
                initial_soc,
                final_threshold,
                start_time,
                lst,
                res,
                last_leg,
                night_travel,
                time_end,
                marker_lst_alt,
                    markers_alt,
                    mid_lat,
                    mid_lon,
                    point_list_alt_1,
                    distance_alt_1,
                    time_alt_1,
                    initial_soc,
                    final_threshold,
                    start_time,
                    lst_alt_1,
                    res_alt,
                    last_leg_alt,
                    night_travel_alt,
                    time_end_alt )      
