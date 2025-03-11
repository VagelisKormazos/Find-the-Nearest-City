# Find the Nearest City

## 🌍 Overview
Find the Nearest City is a Python-based simulation that identifies and visualizes crisis and safe zones on a map. Using geospatial data and simulations, it helps determine the closest city or safe zone from a given crisis point.

## 🚀 Features
- Identifies crisis and safe zones on a map.
- Uses geospatial data (GeoPandas, Shapely) to locate cities.
- Simulates population movement toward safe zones.
- Generates visualizations using Matplotlib and Pygame.

## 🛠 Installation
### Prerequisites
Ensure you have **Python 3.8+** installed along with the required dependencies:

```bash
pip install numpy pygame geopandas matplotlib imageio shapely
```

### Clone the Repository
```bash
git clone https://github.com/your-username/Find-the-nearest-City.git
cd Find-the-nearest-City
```

## 🔧 Usage
Run the simulation with:
```bash
python app.py
```

## 📌 Project Structure
```
Find-the-nearest-City/
│── classes/
│   │── zone.py
│   │── individual.py
│   │── CountryLocator.py
│   │── RestCountriesAPI.py
│   │── CrisisSimulation.py
│── README.md
│── requirements.txt
│── app.py
```

## 📷 Example Output
The simulation generates a map with marked crisis zones (🔴) and safe zones (🟢), showing the movement of individuals.

![image](https://github.com/user-attachments/assets/a01255b5-8ad0-412d-92c9-2ae8378cff71)

## 💡 Future Improvements
- Add real-time crisis data integration.
- Improve movement dynamics.
- Implement an interactive UI.

## 📜 License
This project is licensed under the MIT License.

---
💬 Feel free to contribute by opening an issue or submitting a pull request!

