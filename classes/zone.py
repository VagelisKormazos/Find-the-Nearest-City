# This Python class provides fundamental computational functionality for the 
# represenation of both safe and crisis zones.

# Import required Python modules.
import pygame
import numpy as np
import geopandas as gpd
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

class Zone:
    def __init__(self, center, radius, zone_type='crisis'):
        self.center = np.array(center)
        self.radius = radius
        self.zone_type = zone_type  # 'crisis' or 'safe'

    def draw(self, screen, scale_factor, color):
        pygame.draw.circle(screen, color, (int(self.center[0] * scale_factor), int(self.center[1] * scale_factor)),
                           int(self.radius * scale_factor), 2)
        
    def get_center(self):
        #print(self.center[0], self.center[1])
        return (self.center[0], self.center[1])

    def locate_country(self, zone):
        # Δημιουργία σημείου από το κέντρο της ζώνης κρίσης
        point = gpd.points_from_xy([zone.get_center()[0]], [zone.get_center()[1]])