import pygame
import pygame.gfxdraw
import math
from typing import Dict, List, Tuple, Optional
import threading
import time
from core.light_effect import LightEffect

class LEDSimulator:
    """
    Class to simulate LED tape light visually
    """
    
    def __init__(self, controller: LightEffect, width: int = 1280, height: int = 240, 
                 led_size: int = 20, led_spacing: int = 5, bg_color: Tuple[int, int, int] = (10, 10, 15)):
        """
        Initialize the LED simulator
        
        Args:
            controller: LightEffect instance to simulate
            width: Width of the simulator window
            height: Height of the simulator window
            led_size: Size of each LED
            led_spacing: Spacing between LEDs
            bg_color: Background color of the simulator
        """
        pygame.init()

        self.width = width
        self.height = height
        self.led_size = led_size
        self.led_spacing = led_spacing
        self.bg_color = bg_color
        self.led_count = controller.led_count
        self.controller = controller
        

        total_led_width = (self.led_size + self.led_spacing) * self.led_count - self.led_spacing
        
        if total_led_width > width:
            self.width = total_led_width + 40
        
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        pygame.display.set_caption("LED Tape Light Simulator")
        
        self.clock = pygame.time.Clock()
        
        self.running = False
        self.thread = None
        
        self.mouse_pos = (0, 0)
        self.highlighted_led = -1
        
        self.glow_factor = 1.2
        self.reflection_height = int(self.height * 0.2)
        self.reflection_fade = 0.3 
        
        self.font = pygame.font.SysFont('Arial', 12)
        self.info_font = pygame.font.SysFont('Arial', 16)
        
        self.animation_time = 0
        self.wave_amplitude = 5
        self.wave_frequency = 0.2
        
    def start(self):
        """
        Start the simulation in a separate thread
        """
        if self.running:
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._run_simulation)
        self.thread.daemon = True
        self.thread.start()
    
    def stop(self):
        """
        Stop the simulation
        """
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
            
        pygame.quit()
    
    def _run_simulation(self):
        """
        Main simulation loop
        """
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.VIDEORESIZE:
                    self.width, self.height = event.size
                    self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
                    self.reflection_height = int(self.height * 0.2)
                elif event.type == pygame.MOUSEMOTION:
                    self.mouse_pos = event.pos
            
            self.animation_time += 0.05
            
            self.controller.update_all()
            
            led_colors = self.controller.get_led_output()
            
            self.screen.fill(self.bg_color)
            
            self._draw_bg_gradient()
            
            self.highlighted_led = self._get_led_at_position(self.mouse_pos)
            
            self._draw_leds(led_colors)
            
            self._draw_segments_visualization()

            fps = self.clock.get_fps()
            fps_text = self.info_font.render(f"FPS: {fps:.1f}", True, (200, 200, 200))
            self.screen.blit(fps_text, (10, 10))

            count_text = self.info_font.render(f"LEDs: {self.led_count}", True, (200, 200, 200))
            self.screen.blit(count_text, (10, 30))

            pygame.display.flip()

            self.clock.tick(self.controller.fps)
    
    def _get_led_at_position(self, pos: Tuple[int, int]) -> int:
        """
        Get the LED index at a given position
        
        Args:
            pos: Position (x, y)
            
        Returns:
            LED index or -1 if no LED at position
        """
        x, y = pos
        
        led_total_width = self.led_size + self.led_spacing
        
        start_x = (self.width - (led_total_width * self.led_count - self.led_spacing)) // 2

        if y < self.height // 2 - self.led_size or y > self.height // 2 + self.led_size:
            return -1

        if x < start_x or x > start_x + led_total_width * self.led_count - self.led_spacing:
            return -1

        index = (x - start_x) // led_total_width
        
        if 0 <= index < self.led_count:
            return index
            
        return -1
    
    def _draw_bg_gradient(self):
        """
        Draw a subtle background gradient
        """
        for y in range(self.height):
            intensity = y / self.height
            color = (
                int(self.bg_color[0] * (1 + intensity * 0.1)),
                int(self.bg_color[1] * (1 + intensity * 0.1)),
                int(self.bg_color[2] * (1 + intensity * 0.2))
            )
            pygame.draw.line(self.screen, color, (0, y), (self.width, y))
    
    def _draw_leds(self, led_colors: List[List[int]]):
        """
        Draw all LEDs with their colors and effects
        
        Args:
            led_colors: List of RGB values for each LED
        """
        led_total_width = self.led_size + self.led_spacing

        start_x = (self.width - (led_total_width * self.led_count - self.led_spacing)) // 2
        center_y = self.height // 2

        tape_rect = pygame.Rect(
            start_x - 5, 
            center_y - self.led_size // 2 - 5,
            led_total_width * self.led_count - self.led_spacing + 10,
            self.led_size + 10
        )
        pygame.draw.rect(self.screen, (30, 30, 30), tape_rect, border_radius=5)

        strip_rect = pygame.Rect(
            start_x - 5, 
            center_y - 1,
            led_total_width * self.led_count - self.led_spacing + 10,
            2
        )
        pygame.draw.rect(self.screen, (50, 50, 50), strip_rect)

        for i in range(self.led_count):
            x = start_x + i * led_total_width
            y = center_y

            if i < len(led_colors):
                color = led_colors[i]
            else:
                color = [0, 0, 0]

            wave_offset = math.sin(self.animation_time + i * 0.2) * self.wave_amplitude

            glow_color = [min(255, int(c * self.glow_factor)) for c in color]
            
            if any(c > 20 for c in color):
                brightness = sum(color) / 3 / 255
                glow_radius = int(self.led_size * (0.8 + brightness * 0.5))

                for radius in range(glow_radius, 0, -2):
                    alpha = int(100 * (radius / glow_radius) * brightness)
                    glow_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                    pygame.draw.circle(glow_surface, (*glow_color, alpha), (radius, radius), radius)
                    self.screen.blit(glow_surface, (x + self.led_size//2 - radius, y - radius + wave_offset))

            pygame.draw.circle(self.screen, color, (x + self.led_size//2, y + wave_offset), self.led_size//2)

            pygame.draw.circle(self.screen, (50, 50, 50), (x + self.led_size//2, y + wave_offset), self.led_size//2, 1)
            
            if sum(color) > 200:
                highlight_pos = (x + self.led_size//2 - self.led_size//4, y + wave_offset - self.led_size//4)
                highlight_radius = self.led_size // 6
                pygame.draw.circle(self.screen, (255, 255, 255, 150), highlight_pos, highlight_radius)

            reflection_alpha = int(255 * self.reflection_fade * (sum(color) / (255 * 3)))
            if reflection_alpha > 10:
                reflection_surface = pygame.Surface((self.led_size, self.reflection_height), pygame.SRCALPHA)
                for ry in range(self.reflection_height):
                    line_alpha = reflection_alpha * (1 - ry / self.reflection_height)
                    reflection_color = (*color, int(line_alpha))
                    pygame.draw.line(
                        reflection_surface,
                        reflection_color,
                        (self.led_size//2, ry),
                        (self.led_size//2, ry),
                        1
                    )
                self.screen.blit(reflection_surface, (x, y + self.led_size//2 + wave_offset))

            if i == self.highlighted_led:
                pygame.draw.circle(
                    self.screen, 
                    (255, 255, 255), 
                    (x + self.led_size//2, y + wave_offset), 
                    self.led_size//2 + 2, 
                    2
                )

                info_text = f"LED #{i}: RGB({color[0]}, {color[1]}, {color[2]})"
                text_surface = self.info_font.render(info_text, True, (255, 255, 255))
                text_rect = text_surface.get_rect(center=(x + self.led_size//2, y - 20 + wave_offset))
                bg_rect = text_rect.copy()
                bg_rect.inflate_ip(10, 6)
                pygame.draw.rect(self.screen, (0, 0, 0, 150), bg_rect, border_radius=4)
                self.screen.blit(text_surface, text_rect)
    
    def _draw_segments_visualization(self):
        """
        Draw a visualization of active segments
        """
        if not self.controller.segments:
            return
            
        segment_height = 30
        y_pos = self.height - segment_height - 10

        led_total_width = self.led_size + self.led_spacing

        start_x = (self.width - (led_total_width * self.led_count - self.led_spacing)) // 2
        total_width = led_total_width * self.led_count - self.led_spacing
        
        bar_rect = pygame.Rect(start_x - 5, y_pos - 5, total_width + 10, segment_height + 10)
        pygame.draw.rect(self.screen, (20, 20, 30), bar_rect, border_radius=5)

        title_text = self.info_font.render("Active Segments", True, (200, 200, 200))
        title_rect = title_text.get_rect(midtop=(start_x + total_width//2, y_pos - 25))
        self.screen.blit(title_text, title_rect)

        segment_colors = [
            (255, 50, 50),   # Red
            (50, 255, 50),   # Green
            (50, 50, 255),   # Blue
            (255, 255, 50),  # Yellow
            (255, 50, 255),  # Magenta
            (50, 255, 255),  # Cyan
            (255, 150, 50),  # Orange
            (150, 50, 255),  # Purple
        ]
        
        for i, (segment_id, segment) in enumerate(self.controller.segments.items()):

            segment_start = max(0, min(self.led_count - 1, int(segment.current_position)))
            segment_end = max(0, min(self.led_count - 1, 
                               int(segment.current_position + sum(segment.length) * segment.direction)))
            
            if segment_start > segment_end:
                segment_start, segment_end = segment_end, segment_start
            
            pixel_start = start_x + segment_start * led_total_width
            pixel_width = (segment_end - segment_start) * led_total_width

            color_idx = i % len(segment_colors)
            segment_color = segment_colors[color_idx]
            
            pygame.draw.rect(
                self.screen,
                segment_color,
                (pixel_start, y_pos, pixel_width, segment_height),
                border_radius=5
            )
            
            id_text = self.font.render(f"ID: {segment_id}", True, (255, 255, 255))
            self.screen.blit(id_text, (pixel_start + 5, y_pos + 5))
            
            speed_text = self.font.render(f"Speed: {segment.move_speed:.1f}", True, (255, 255, 255))
            self.screen.blit(speed_text, (pixel_start + 5, y_pos + 5 + id_text.get_height()))

    def resize(self, width: int, height: int):
        """
        Resize the simulator window
        
        Args:
            width: New width
            height: New height
        """
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
        self.reflection_height = int(self.height * 0.2)