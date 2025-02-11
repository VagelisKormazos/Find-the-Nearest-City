import numpy as np
import pygame
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import imageio  # For saving GIF
from classes.zone import Zone
from classes.individual import Individual
from classes.CountryLocator import CountryLocator
from shapely.geometry import Point
from classes.RestCountriesAPI import RestCountriesAPI  # Εισάγουμε την κλάση RestCountriesAPI
from shapely.geometry import Point


# Simulation class to manage the entire simulation
class Simulation:
    def __init__(self, grid_size, population_size, repulsion_strength_crisis, attraction_strength_safe, noise_strength, stop_threshold=1e-2):
        self.grid_size = grid_size
        self.population_size = population_size
        self.repulsion_strength_crisis = repulsion_strength_crisis
        self.attraction_strength_safe = attraction_strength_safe
        self.noise_strength = noise_strength
        self.stop_threshold = stop_threshold  # Threshold for detecting when movement stops
        self.individuals = []
        self.crisis_zones = []
        self.safe_zones = []
        self.screen = None
        self.scale_factor = None
        self.map_image_path = "zoomed_area_map.png"
        self.frames = []  # List to store frames

        # Load the world shapefile and initialize CountryLocator
        self.world = gpd.read_file("naturalearth_lowres/ne_110m_admin_0_countries.shp")
        self.country_locator = CountryLocator(self.world)

        # Δημιουργία αντικειμένου RestCountriesAPI
        self.rest_countries_api = RestCountriesAPI()

    def load_and_display_map(self):
        # Add a print to ensure this part is executed
        world = gpd.read_file("naturalearth_lowres/ne_110m_admin_0_countries.shp")
        print(world.crs)  # Check the CRS
        
        # Define a bounding box (xmin, ymin, xmax, ymax) for zooming in on a region
        bbox = (-10, 10, 25, 25)  # Example bounding box: Europe (adjust as needed)
        zoomed_area = self.world.cx[bbox[0]:bbox[2], bbox[1]:bbox[3]]

        # Plot the zoomed-in map and country names
        fig, ax = plt.subplots(figsize=(10, 10))
        zoomed_area.boundary.plot(ax=ax, color='black')

        country_name_column = 'ADMIN'  # Updated to 'ADMIN'
        zoomed_area.apply(lambda x: ax.text(x.geometry.centroid.x, x.geometry.centroid.y,
                                             x[country_name_column], fontsize=8, fontproperties=FontProperties(weight='bold')),
                          axis=1)
        ax.set_title('Zoomed-in Map')
        ax.set_axis_off()

        # Save the map as an image to use in Pygame
        plt.savefig(self.map_image_path, bbox_inches='tight', pad_inches=0)
        plt.close()

    def generate_zones(self):
        min_latitude = 10.0
        min_longitude = 3.0

        # Δημιουργία τυχαίων κρίσιμων ζωνών
        self.crisis_zones = [
            Zone(np.random.uniform([20, 20], [80, 80]), 2, 'crisis'),
            Zone(np.random.uniform([40, 40], [60, 60]), 2, 'crisis')
        ]
        
        print("Crisis Centers:")
        self.safe_zones = []

        for zone in self.crisis_zones:
            center = zone.get_center()
            geo_point = (
                min_longitude + (center[0] / 4.5),  # Χ
                min_latitude + (center[1] / 5)      # Υ
            )

            # Βρίσκουμε τη χώρα και τους γείτονές της
            country_name, neighbors = self.country_locator.locate_country(geo_point)
            print(f"Country for Crisis Center: {country_name}")
            print(f"Neighbors: {neighbors}")

            # Επιλέγουμε έναν ή δύο γείτονες για τον Safe Center
            num_safe_centers = np.random.choice([1, 2])
            selected_neighbors = np.random.choice(neighbors, size=min(num_safe_centers, len(neighbors)), replace=False)

            for neighbor in selected_neighbors:
                # Καλούμε το RestCountriesAPI για να βρούμε τις συντεταγμένες της πρωτεύουσας του γείτονα
                capital_coords = self.rest_countries_api.get_capital_coordinates(neighbor)
                
                if capital_coords:  # Αν επιστραφούν συντεταγμένες πρωτεύουσας
                    safe_zone = Zone([capital_coords.x, capital_coords.y], 2, 'safe')
                    self.safe_zones.append(safe_zone)
                    print(f"Safe Center in Neighbor {neighbor} at Capital: {capital_coords}")
                else:
                    print(f"No capital found for {neighbor}")

    # Νέα μέθοδος για την εύρεση ενός τυχαίου σημείου εντός της χώρας
    def get_random_point_within(self, polygon):
        """Returns a random point within a given polygon."""
        minx, miny, maxx, maxy = polygon.bounds
        while True:
            point = Point(np.random.uniform(minx, maxx), np.random.uniform(miny, maxy))
            if polygon.contains(point):
                return point

    
    def initialize_individuals(self):
        num_blue = int(self.population_size * 0.50)  # 50% μπλε (κανονική ταχύτητα)
        num_orange = int(self.population_size * 0.35)  # 35% πορτοκαλί (πιο αργά)
        num_red = self.population_size - num_blue - num_orange  # 15% κόκκινα (πολύ αργά)

        for _ in range(num_blue):
            zone = np.random.choice(self.crisis_zones)
            angle = np.random.uniform(0, 2 * np.pi)
            distance_from_center = np.random.uniform(0, zone.radius)
            x = zone.center[0] + distance_from_center * np.cos(angle)
            y = zone.center[1] + distance_from_center * np.sin(angle)
            self.individuals.append(Individual([x, y], speed_factor=1.0))  # Μπλε

        for _ in range(num_orange):
            zone = np.random.choice(self.crisis_zones)
            angle = np.random.uniform(0, 2 * np.pi)
            distance_from_center = np.random.uniform(0, zone.radius)
            x = zone.center[0] + distance_from_center * np.cos(angle)
            y = zone.center[1] + distance_from_center * np.sin(angle)
            self.individuals.append(Individual([x, y], speed_factor=0.6))  # Πορτοκαλί

        for _ in range(num_red):
            zone = np.random.choice(self.crisis_zones)
            angle = np.random.uniform(0, 2 * np.pi)
            distance_from_center = np.random.uniform(0, zone.radius)
            x = zone.center[0] + distance_from_center * np.cos(angle)
            y = zone.center[1] + distance_from_center * np.sin(angle)
            self.individuals.append(Individual([x, y], speed_factor=0.3))  # Κόκκινο


    def draw_zones(self):
        for zone in self.crisis_zones:
            zone.draw(self.screen, self.scale_factor, color=(255, 0, 0))  # Red for crisis zones
        for zone in self.safe_zones:
            zone.draw(self.screen, self.scale_factor, color=(0, 255, 0))  # Green for safe zones

    def update_individuals(self, prev_positions):
        all_positions_changed = True
        new_positions = []
        
        for individual in self.individuals:
            prev_position = individual.position.copy()
            force = individual.apply_forces(self.crisis_zones, self.safe_zones,
                                            self.repulsion_strength_crisis, self.attraction_strength_safe)
            individual.update_position(force, self.noise_strength, self.grid_size)
            new_positions.append(individual.position)

            # Check if the position change is below the threshold
            position_change = np.linalg.norm(individual.position - prev_position)
            if position_change > self.stop_threshold:
                all_positions_changed = False

        return all_positions_changed, new_positions

    def draw_individuals(self):
        for individual in self.individuals:
            individual.draw(self.screen, self.scale_factor)

    def draw_grid(self):
        grid_color = (0, 0, 0, 100)  # RGBA with alpha for transparency
        grid_surface = pygame.Surface((width, height), pygame.SRCALPHA)  # Enable alpha blending
        cell_size = width // 10  # Create 10x10 grid cells
        
        for x in range(0, width, cell_size):
            pygame.draw.line(grid_surface, grid_color, (x, 0), (x, height))  # Draw vertical lines
        for y in range(0, height, cell_size):
            pygame.draw.line(grid_surface, grid_color, (0, y), (width, y))  # Draw horizontal lines
        
        self.screen.blit(grid_surface, (0, 0))  # Overlay the grid on the main screen

    def save_frame(self):
        """Captures the current screen and saves it as an image for creating a GIF later."""
        frame = pygame.surfarray.array3d(self.screen)
        frame = np.transpose(frame, (1, 0, 2))  # Pygame uses a different axis ordering
        self.frames.append(frame)

    def save_gif(self, filename="simulation.gif"):
        """Creates a GIF from the captured frames."""
        imageio.mimsave(filename, self.frames, fps=10)

    def run(self):
        pygame.init()
        global width, height
        width, height = 800, 800
        self.screen = pygame.display.set_mode((width, height))
        clock = pygame.time.Clock()
        self.scale_factor = width / self.grid_size

        # Load and display the zoomed-in map
        self.load_and_display_map()

        # Load the saved map as background
        background = pygame.image.load(self.map_image_path)
        background = pygame.transform.scale(background, (width, height))

        # Initialize zones and individuals
        self.generate_zones()
        self.initialize_individuals()

        # Initialize variables to track position changes
        prev_positions = [individual.position.copy() for individual in self.individuals]

        # Main simulation loop
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            # Clear the screen and draw everything
            self.screen.blit(background, (0, 0))  # Draw the map background
            self.draw_zones()
            all_positions_changed, new_positions = self.update_individuals(prev_positions)
            self.draw_individuals()
            self.draw_grid()

            # Capture the current frame for GIF
            self.save_frame()

            # Check if the positions have stopped changing
            if all_positions_changed:
                print("Simulation stopped as individuals stopped moving.")
                running = False

            # Update previous positions
            prev_positions = new_positions

            # Update the display
            pygame.display.flip()

            # Control the frame rate
            clock.tick(30)  # 30 frames per second

        # Save the captured frames as a GIF
        self.save_gif(filename="simulation.gif")

        # Clean up and close the Pygame window
        pygame.quit()

# Create a Simulation instance and run it
simulation = Simulation(grid_size=100, population_size=500,
                        repulsion_strength_crisis=0.1, attraction_strength_safe=0.05, noise_strength=0.02)
simulation.run()
