import geopandas as gpd
from shapely.geometry import Point
from shapely.geometry import Point

class CountryLocator:
    def __init__(self, world):
        # Ensure the world GeoDataFrame is in EPSG:4326
        if world.crs != "EPSG:4326":
            self.world = world.to_crs("EPSG:4326")
        else:
            self.world = world

    def locate_country(self, geo_point):
        # Confirm `geo_point` is a tuple (longitude, latitude)
        point = Point(geo_point[0], geo_point[1])  # Use geo_point directly
        #print(f"Geo Point: {geo_point}")

        # Find the country containing the point
        country = self.world[self.world.contains(point)]

        if not country.empty:
            country_name = country['ADMIN'].values[0]  # Retrieve the country name
            #print(f"Found country: {country_name} for point {point}")
            neighbors = self.get_neighbors(country_name)  # Get neighboring countries
            #print(f"Neighbors of {country_name}: {neighbors}")
            return country_name, neighbors
        else:
            print(f"No country found for point {point}")
        return None, []

    def get_neighbors(self, country_name):
        # Get geometry of the specified country
        country_geom = self.world[self.world['ADMIN'] == country_name].geometry.values[0]

        # Find neighboring countries that touch this country's geometry
        neighbors = self.world[self.world.touches(country_geom)]['ADMIN'].tolist()
        print(f"Neighbors of {country_name} are: {neighbors}")
        return neighbors

 