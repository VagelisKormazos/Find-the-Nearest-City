import requests
from shapely.geometry import Point

class RestCountriesAPI:
    def __init__(self):
        pass

    def get_capital_coordinates(self, country_name):
        """Επιστρέφει τις συντεταγμένες της πρωτεύουσας της χώρας."""
        url = f"https://restcountries.com/v3.1/name/{country_name}?fields=capitalInfo"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            # Ελέγχουμε αν υπάρχει η πρωτεύουσα και αν υπάρχουν συντεταγμένες
            if 'capitalInfo' in data[0] and 'latlng' in data[0]['capitalInfo']:
                lat, lon = data[0]['capitalInfo']['latlng']
                return Point(lon, lat)  # Επιστρέφει το Point με τις συντεταγμένες
        return None  # Αν δεν βρεθούν συντεταγμένες, επιστρέφει None


    # Παράδειγμα χρήσης:
    #capital_coords = get_capital_coordinates("Niger")
    #print(capital_coords)  # Θα επιστρέψει κάτι σαν Point(2.11, 13.51)
