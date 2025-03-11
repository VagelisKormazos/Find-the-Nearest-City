from flask import Flask, render_template, request, jsonify
import folium
import geopandas as gpd
import numpy as np
from shapely.geometry import box


app = Flask(__name__)

# Φόρτωση των δεδομένων
rivers = gpd.read_file('natural_earth_vector/10m_physical/ne_10m_rivers_lake_centerlines.shp')
lakes = gpd.read_file('natural_earth_vector/10m_physical/ne_10m_lakes.shp')
cities = gpd.read_file('natural_earth_vector/10m_cultural/ne_10m_populated_places.shp')
roads = gpd.read_file('natural_earth_vector/10m_cultural/ne_10m_roads.shp')
coastline = gpd.read_file('natural_earth_vector/10m_physical/ne_10m_coastline.shp')

# Συντεταγμένες για την Ελλάδα (περίπου)
GREECE_BOUNDS = box(19.0, 34.0, 29.6, 41.8)

def get_random_point():
    """Επιστρέφει ένα τυχαίο σημείο εντός της Ελλάδας."""
    minx, miny, maxx, maxy = GREECE_BOUNDS.bounds
    while True:
        random_lat = np.random.uniform(miny, maxy)
        random_lng = np.random.uniform(minx, maxx)
        point = gpd.GeoSeries([gpd.points_from_xy([random_lng], [random_lat])[0]])
        if GREECE_BOUNDS.contains(point).all():
            return random_lat, random_lng


def find_nearest_city(crisis_point):
    """Βρίσκει την πλησιέστερη πόλη στο σημείο κρίσης."""
    if crisis_point.crs is None:
        crisis_point.set_crs('EPSG:4326', allow_override=True, inplace=True)
    
    crisis_point_projected = crisis_point.to_crs(epsg=3857)
    cities_projected = cities.to_crs(epsg=3857)

    cities_projected['distance'] = cities_projected.geometry.distance(crisis_point_projected.geometry.iloc[0])
    nearest_city = cities_projected.loc[cities_projected['distance'].idxmin()]

    # Εκτύπωση για έλεγχο
    print(f"Nearest City: {nearest_city['NAME']}, Distance: {nearest_city['distance']} meters")
    
    return nearest_city

def create_map():
    """Δημιουργεί έναν διαδραστικό χάρτη της Ελλάδας."""
    m = folium.Map(location=[39.0742, 21.8243], zoom_start=6)

    # Προσθήκη των datasets στον χάρτη
    folium.GeoJson(rivers, name='Rivers', style_function=lambda x: {'color': 'blue'}).add_to(m)
    folium.GeoJson(lakes, name='Lakes', style_function=lambda x: {'color': 'lightblue', 'fill': True}).add_to(m)
    folium.GeoJson(coastline, name='Coastline', style_function=lambda x: {'color': 'black'}).add_to(m)
    folium.GeoJson(roads, name='Roads', style_function=lambda x: {'color': 'gray'}).add_to(m)

    # Προσθήκη των πόλεων ως markers
    for _, city in cities.iterrows():
        folium.CircleMarker(
            location=[city.geometry.y, city.geometry.x],
            radius=3,
            color='red',
            fill=True,
            popup=city['NAME']
        ).add_to(m)

    # Δημιουργία τυχαίου σημείου κρίσης
    crisis_lat, crisis_lng = get_random_point()
    crisis_point = gpd.GeoSeries([gpd.points_from_xy([crisis_lng], [crisis_lat])[0]])

    # Προσθήκη του σημείου κρίσης στον χάρτη
    folium.Marker(
        location=[crisis_lat, crisis_lng],
        icon=folium.Icon(color="red", icon="exclamation-triangle", prefix='fa'),
        popup="Crisis Point"
    ).add_to(m)

    # Βρίσκουμε την πλησιέστερη πόλη
    nearest_city = find_nearest_city(crisis_point)

    # Μετατροπή της σειράς nearest_city σε GeoDataFrame
    nearest_city_gdf = gpd.GeoDataFrame([nearest_city], crs='EPSG:3857')

    # Μετατροπή των συντεταγμένων από EPSG:3857 σε EPSG:4326
    nearest_city_4326 = nearest_city_gdf.to_crs(epsg=4326)

    # Προσθήκη του πράσινου σημείου στην πλησιέστερη πόλη
    folium.Marker(
        location=[nearest_city_4326.geometry.y.iloc[0], nearest_city_4326.geometry.x.iloc[0]],
        icon=folium.Icon(color="green", icon="leaf", prefix='fa'),
        popup=nearest_city_4326['NAME'].iloc[0]
    ).add_to(m)

    # Προσθήκη γραμμής που ενώνει το σημείο κρίσης με την πλησιέστερη πόλη
    folium.PolyLine(
        locations=[[crisis_lat, crisis_lng], [nearest_city_4326.geometry.y.iloc[0], nearest_city_4326.geometry.x.iloc[0]]],
        color='red',
        weight=2.5,
        opacity=1
    ).add_to(m)

    # Υπολογισμός του μέσου της γραμμής
    mid_lat = (crisis_lat + nearest_city_4326.geometry.y.iloc[0]) / 2
    mid_lng = (crisis_lng + nearest_city_4326.geometry.x.iloc[0]) / 2

    # Προσθήκη του σημείου στο μέσο της γραμμής
    folium.Marker(
        location=[mid_lat, mid_lng],
        icon=folium.Icon(color="blue", icon="user", prefix='fa'),
        popup="Mid Point"
    ).add_to(m)

    folium.LayerControl().add_to(m)
    return m._repr_html_()


@app.route('/')
def home():
    map_html = create_map()
    return render_template('index.html', map_html=map_html)

@app.route('/random_crisis', methods=['GET'])
def random_crisis():
    crisis_lat, crisis_lng = get_random_point()
    return jsonify({"lat": crisis_lat, "lng": crisis_lng})

if __name__ == '__main__':
    app.run(debug=True)
