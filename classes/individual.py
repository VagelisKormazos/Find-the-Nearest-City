import numpy as np
import pygame
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class Individual:
    def __init__(self, position, speed_factor=1.0):
        self.position = np.array(position)
        self.speed_factor = speed_factor  # Ταχύτητα μετακίνησης

    def apply_forces(self, crisis_zones, safe_zones, repulsion_strength_crisis, attraction_strength_safe):
        total_repulsion = np.zeros(2)
        for crisis_zone in crisis_zones:
            dist_to_crisis = np.linalg.norm(self.position - crisis_zone.center)
            if dist_to_crisis < crisis_zone.radius:
                repulsion = (self.position - crisis_zone.center) * repulsion_strength_crisis / (dist_to_crisis + 1e-3)
                total_repulsion += repulsion

        closest_safe_zone = min(safe_zones, key=lambda zone: np.linalg.norm(self.position - zone.center))
        dist_to_safe = np.linalg.norm(self.position - closest_safe_zone.center)
        attraction = (closest_safe_zone.center - self.position) * attraction_strength_safe / (dist_to_safe + 1e-3)

        force = total_repulsion + attraction
        return force

    def update_position(self, force, noise_strength, grid_size):
        noise = np.random.randn(2) * noise_strength
        self.position += (force + noise) * self.speed_factor  # Εφαρμογή της ταχύτητας
        self.position = np.clip(self.position, 0, grid_size)

    def draw(self, screen, scale_factor):
        if self.speed_factor == 1.0:
            color = (0, 0, 255)  # Μπλε (κανονική ταχύτητα)
        elif self.speed_factor == 0.6:
            color = (255, 165, 0)  # Πορτοκαλί (πιο αργά)
        else:
            color = (255, 0, 0)  # Κόκκινο (πολύ αργά)

        pygame.draw.circle(screen, color, (int(self.position[0] * scale_factor), int(self.position[1] * scale_factor)), 3)
