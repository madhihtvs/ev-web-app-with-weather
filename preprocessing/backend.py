import pandas as pd
import requests
import flexpolyline as fp
from datetime import date
from scipy.spatial.distance import cdist

def get_coordinates(location):
    """Getting coordinates from address"""
    API = "FIAqwEHj3qFBbqhhKYS4PYfaeR_8thfqZiabEhWhyc4"
    location_format = location.replace(" ", "+")
    url = f"https://geocode.search.hereapi.com/v1/geocode?q={location_format}&apiKey={API}"

    resp = requests.get(url=url)
    data = resp.json()

    return data


def get_address(lat, lon):
    """Getting address from coordinates to be added to marker"""
    API = "FIAqwEHj3qFBbqhhKYS4PYfaeR_8thfqZiabEhWhyc4"
    url = f"https://revgeocode.search.hereapi.com/v1/revgeocode?at={lat}%2C{lon}&apiKey={API}&lang=en-US"
    
    resp = requests.get(url=url)
    data = resp.json()
 
    address = data["items"][0]['address']['label']
    return address


def get_POI(lat, lon, radius):
    """Getting Points of Interest when specified latitude, longitude and radius"""
    API = "FIAqwEHj3qFBbqhhKYS4PYfaeR_8thfqZiabEhWhyc4"
    url = f"https://discover.search.hereapi.com/v1/discover?limit=20&q=eat-drink,going-out,sights-museums,shopping,leisure-outdoor&in=circle:{lat},{lon};r={radius}&apiKey={API}"
    
    resp = requests.get(url=url)
    data = resp.json()


    POI = []
    for i in range(len(data['items'])):
        name = data["items"][i]['title']
        category = data["items"][i]['categories'][0]['name']
        lat = data["items"][i]['position']['lat']
        lng = data["items"][i]['position']['lng']
        POI.append([name, category, lat, lng])
    
    df = pd.DataFrame(POI, columns = ["Name","Category","Latitude", "Longitude"])

    return df



def get_Hotel(lat, lon):
    """Getting places of accommmodation given a latitude and longitude with a specific radius of 5000km"""
    API = "FIAqwEHj3qFBbqhhKYS4PYfaeR_8thfqZiabEhWhyc4"
    url = f"https://discover.search.hereapi.com/v1/discover?limit=20&q=accommodation&in=circle:{lat},{lon};r=5000&apiKey={API}"
    
    resp = requests.get(url=url)
    data = resp.json()


    POI = []
    for i in range(len(data['items'])):
        name = data["items"][i]['title']
        category = data["items"][i]['categories'][0]['name']
        lat = data["items"][i]['position']['lat']
        lng = data["items"][i]['position']['lng']
        POI.append([name, category, lat, lng])

    df = pd.DataFrame(POI, columns = ["Name","Category","Latitude", "Longitude"])
    return df


    
def get_route(orig_lat, orig_lon, dest_lat, dest_lon):
    """Get polyline path between origin and destination. Also return total distance and total time together with list of coordinates"""
    API = "FIAqwEHj3qFBbqhhKYS4PYfaeR_8thfqZiabEhWhyc4"
    url = f"https://router.hereapi.com/v8/routes?transportMode=scooter&scooter[allowHighway]=true&origin={orig_lat},{orig_lon}&destination={dest_lat},{dest_lon}&return=polyline,summary&apikey={API}"
    response = requests.request("GET", url)
    data = response.json()
    polyline = data["routes"][0]['sections'][0]['polyline']
    lst = fp.decode(polyline)
    distance = data['routes'][0]['sections'][0]['summary']['length']
    distance = distance / 1000
    time = data['routes'][0]['sections'][0]['summary']['duration']
    return lst, distance, time


def get_route_short(orig_lat, orig_lon, dest_lat, dest_lon):
    """Get polyline path between origin and destination which is shorter than the default. Also return total distance and total time together with list of coordinates"""
    API = "FIAqwEHj3qFBbqhhKYS4PYfaeR_8thfqZiabEhWhyc4"
    url = f"https://router.hereapi.com/v8/routes?transportMode=car&routingMode=short&origin={orig_lat},{orig_lon}&destination={dest_lat},{dest_lon}&return=polyline,summary&apikey={API}"
    response = requests.request("GET", url)
    data = response.json()
    polyline = data["routes"][0]['sections'][0]['polyline']
    lst = fp.decode(polyline)
    distance = data['routes'][0]['sections'][0]['summary']['length']
    distance = distance / 1000
    time = data['routes'][0]['sections'][0]['summary']['duration']
    return lst, distance, time


def get_route_many(*points):
    """Get polyline path between multiple points (No Limit). Also return total distance and total time together with list of coordinates"""
    
    string = ""
    lst = points[0]
    orig_lat = lst[0][0]
    orig_lon = lst[0][1]
    dest_lat = lst[-1][0]
    dest_lon = lst[-1][1]
    points = points[0]
    del points[0]
    del points[-1]
    for i in points:
        lat = i[0]
        lng = i[1]
        string += f"&via={lat},{lng}"
    
    API = "FIAqwEHj3qFBbqhhKYS4PYfaeR_8thfqZiabEhWhyc4"
    url = f"https://router.hereapi.com/v8/routes?transportMode=scooter&origin={orig_lat},{orig_lon}&destination={dest_lat},{dest_lon}{string}&return=polyline,summary&apikey={API}"
    response = requests.request("GET", url)
    data = response.json()
    polyline = []
    distance = 0
    time = 0
    for i in range(len(lst)+1):
        polyline_leg = data["routes"][0]['sections'][i]['polyline']
        lst = fp.decode(polyline_leg)
        polyline.extend(lst)
        distance += data['routes'][0]['sections'][i]['summary']['length']
        time += data['routes'][0]['sections'][i]['summary']['duration']
    distance = distance / 1000
    return polyline, distance, time


def get_route_many_short(*points):
    """Get polyline path between multiple points (No Limit) which is shorter than balanced route. Also return total distance and total time together with list of coordinates"""
    string = ""
    lst = points[0]
    orig_lat = lst[0][0]
    orig_lon = lst[0][1]
    dest_lat = lst[-1][0]
    dest_lon = lst[-1][1]
    points = points[0]
    del points[0]
    del points[-1]
    for i in points:
        lat = i[0]
        lng = i[1]
        string += f"&via={lat},{lng}"
    
    API = "FIAqwEHj3qFBbqhhKYS4PYfaeR_8thfqZiabEhWhyc4"
    url = f"https://router.hereapi.com/v8/routes?transportMode=car&routingMode=short&origin={orig_lat},{orig_lon}&destination={dest_lat},{dest_lon}{string}&return=polyline,summary&apikey={API}"
    response = requests.request("GET", url)
    data = response.json()
    polyline = []
    distance = 0
    time = 0
    for i in range(len(lst)+1):
        polyline_leg = data["routes"][0]['sections'][i]['polyline']
        lst = fp.decode(polyline_leg)
        polyline.extend(lst)
        distance += data['routes'][0]['sections'][i]['summary']['length']
        time += data['routes'][0]['sections'][i]['summary']['duration']

    distance = distance / 1000

    return polyline, distance, time




def date_object(date_string):
    date = date_string.split("-")
    return date

def calculate_days(current_date, trip_date):
    current_date = date_object(current_date)
    trip_date = date_object(trip_date)
    d0 = date(int(current_date[0]), int(current_date[1]), int(current_date[2]))
    d1 = date(int(trip_date[0]), int(trip_date[1]), int(trip_date[2]))
    delta = d1 - d0
    return delta.days + 1



def get_weather(df):
    description = []
    rain = []
    for index, row in df.iterrows():
        lat = row["Latitude"]
        lon = row["Longitude"]
        date = row["Date"]
        hour = int(row["Hour"])
        forecast = call_weather_api(lat, lon, date, hour)
        text = forecast['condition']['text']
        precp = forecast['chance_of_rain']
        description.append(text)
        rain.append(precp)
    
    weather_df = pd.DataFrame(list(zip(description, rain)),
               columns =['Weather', 'Chance_of_Rain'])
    weather_df.reset_index(drop=True, inplace=True)
    df = pd.concat([df, weather_df], axis=1)
    return df
    
def call_weather_api(lat, lon, date, hour):
    string = f"{lat},{lon}"
    url = f"http://api.weatherapi.com/v1/forecast.json?key=e264ecec322a4928a7172750222207&q={string}&date={date}&aqi=no&alerts=no"

    resp = requests.get(url=url)
    data = resp.json()
    forecast = data["forecast"]["forecastday"][0]['hour'][hour]
    return forecast
    

def get_severe_weather(df, markers):
    for index, row in df.iterrows():
        if row[-1] > 50:
            markers += "var {idd} = L.marker([{latitude}, {longitude}], weatherOptions_CS);\
                                        {idd}.addTo(map);".format(
                idd=f"weather{index}",
                latitude=row[0],
                longitude=row[1],
            )
            weather = row["Weather"]
            rain = row["Chance_of_Rain"]
            markers += """{idd}.bindPopup("{data}");""".format(idd=f"weather{index}", data = f"Weather:{weather}, Chance of Rain:{rain}")
    return markers


def closest_point(point, points):
    """ Find closest point from a list of points. """
    return points[cdist([point], points).argmin()]


def get_nearest_point(df1, df2):
    df1['point'] = [(x, y) for x,y in zip(df1['Latitude'], df1['Longitude'])]
    df2['point'] = [(x, y) for x,y in zip(df2['Latitude'], df2['Longitude'])]
    df2['closest'] = [closest_point(x, list(df1['point'])) for x in df2['point']]
    return df2