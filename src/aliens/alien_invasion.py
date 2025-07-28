import sys
from time import sleep

import pygame

from aliens.alien import Alien
from aliens.bullet import Bullet
from aliens.button import Button
from aliens.game_stats import GameStats
from aliens.scoreboard import Scoreboard
from aliens.settings import Settings
from aliens.ship import Ship


class AlienInvasion:
    """Overall class to manage game assets and behavior."""

    def __init__(self):
        """Initialize the game, and create game resources."""
        pygame.init()

        # Initialize the game clock
        self.clock = pygame.time.Clock()
        # Game Settings
        self.settings = Settings()
        # Game Window
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)

        # Update screen width and height based on the fullscreen mode
        self.settings.screen_width = self.screen.get_rect().width
        self.settings.screen_height = self.screen.get_rect().height

        pygame.display.set_caption("Alien Invasion")

        # Create an instance to store game statistics, and create a scoreboard
        self.stats = GameStats(self)
        self.sb = Scoreboard(self)

        # Ship, bullets, and aliens
        self.ship = Ship(self)
        self.bullets = pygame.sprite.Group()
        self.aliens = pygame.sprite.Group()
        self._create_fleet()

        # Start Alien Invasion in an inactive state
        self.stats.game_active = False

        # Make the Play button
        self.play_button = Button(self, "Play")

    def run_game(self):
        """Game loop for Alien Invasion."""
        while True:
            self._handle_events()  # handle events
            self._update_objects()  # update the game objects
            self._update_screen()  # update the screen
            self.clock.tick(60)  # set the frame rate to 60 FPS

    def _handle_events(self):
        """Event Handler to respond to keypresses and mouse events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.stats.save_high_score()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                self._handle_keydown_events(event)
            elif event.type == pygame.KEYUP:
                self._handle_keyup_events(event)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self._handle_mouse_events(event)

    def _check_play_button(self, mouse_pos):
        """Check if the Play button has been clicked."""
        button_clicked = self.play_button.rect.collidepoint(mouse_pos)
        return button_clicked and not self.stats.game_active

    def _handle_keydown_events(self, event):
        """Respond to keypresses."""
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = True
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = True
        elif event.key == pygame.K_SPACE:
            self._fire_bullet()
        elif event.key == pygame.K_p:
            self._start_game()
        elif event.key == pygame.K_q:
            self.stats.save_high_score()
            sys.exit()

    def _handle_keyup_events(self, event):
        """Respond to key releases."""
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = False
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = False

    def _handle_mouse_events(self, event):
        """Respond to mouse events."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            if self._check_play_button(mouse_pos):
                self._start_game()

    def _update_ship(self):
        """Update the ship's position."""
        self.ship.update()

    def _fire_bullet(self):
        """Create a new bullet and add it to the bullets group."""
        if len(self.bullets) < self.settings.bullets_allowed:
            new_bullet = Bullet(self)
            self.bullets.add(new_bullet)

    def _update_bullets(self):
        """Update position of bullets and get rid of old bullets."""
        # Update bullet positions
        self.bullets.update()  # calls the update method of each sprite in the group

        # Get rid of bullets that have disappeared
        for bullet in self.bullets.copy():
            if bullet.rect.bottom <= 0:
                self.bullets.remove(bullet)

    def _handle_bullet_alien_collisions(self):
        """Respond to bullet-alien collisions."""
        # Remove any bullets and aliens that have collided
        collisions = pygame.sprite.groupcollide(self.bullets, self.aliens, True, True)

        if collisions:
            for aliens in collisions.values():
                self.stats.score += self.settings.alien_points * len(aliens)
            self.sb.prep_score()
            self.sb.check_high_score()

        # If all aliens are destroyed, start a new level
        if not self.aliens:
            self._start_new_level()

    def _create_fleet(self):
        """Create the fleet of aliens."""
        # Create an alien and keep adding aliens until there's no room left
        # Spacing between aliens is one alien width and one alien height
        alien = Alien(self)
        alien_width, alien_height = alien.rect.size
        current_x, current_y = alien_width, alien_height

        while current_y < (self.settings.screen_height - 6 * alien_height):
            while current_x < (self.settings.screen_width - 2 * alien_width):
                self._create_alien(current_x, current_y)
                current_x += 2 * alien_width
            # Finished a row; reset x value, and increment y value
            current_x = alien_width
            current_y += 2 * alien_height

    def _create_alien(self, x_position, y_position):
        """Create an alien and place it in the row."""
        new_alien = Alien(self)
        new_alien.x = x_position
        new_alien.rect.x = x_position
        new_alien.rect.y = y_position
        self.aliens.add(new_alien)

    def _check_fleet_edges(self):
        """Check if any aliens have reached an edge."""
        for alien in self.aliens.sprites():
            if alien.check_edges():
                return True
        return False

    def _change_fleet_direction(self):
        """Drop the entire fleet and change the fleet's direction."""
        for alien in self.aliens.sprites():
            alien.rect.y += self.settings.fleet_drop_speed
        self.settings.fleet_direction *= -1

    def _update_aliens(self):
        """Check if the fleet is at an edge, then update positions."""
        if self._check_fleet_edges():
            self._change_fleet_direction()
        self.aliens.update()

    def _handle_ship_alien_collisions(self):
        """Respond to ship-alien collisions."""
        # Look for alien-ship collisions
        if pygame.sprite.spritecollideany(self.ship, self.aliens):
            self._ship_hit()

        # Look for aliens hitting the bottom of the screen
        if self._check_aliens_bottom():
            self._ship_hit()  # treat this the same as if the ship got hit

    def _ship_hit(self):
        """Respond to the ship being hit by an alien."""
        if self.stats.ships_left > 0:
            # Decrement ships_left, and update scoreboard
            self.stats.ships_left -= 1
            self.sb.prep_ships()
            self._reset_objects()
            # Pause
            sleep(0.5)
        else:
            self.stats.save_high_score()
            self.stats.game_active = False
            pygame.mouse.set_visible(True)

    def _check_aliens_bottom(self):
        """Check if any aliens have reached the bottom of the screen."""
        screen_rect = self.screen.get_rect()
        for alien in self.aliens.sprites():
            if alien.rect.bottom >= screen_rect.bottom:
                return True
        return False

    def _start_game(self):
        """Start a new game when the player presses 'p' or clicks the Play
        button."""
        if not self.stats.game_active:
            # Reset the game settings
            self.settings.initialize_dynamic_settings()

            # Reset the game statistics
            self.stats.init_stats()
            self.sb.prep_score()
            self.sb.prep_level()
            self.sb.prep_ships()
            self.stats.game_active = True

            # Reset the game elements
            self._reset_objects()

            # Hide the mouse cursor
            pygame.mouse.set_visible(False)

    def _reset_objects(self):
        """Reset the ship, the aliens, and remove the bullets."""
        # Get rid of any remaining aliens and bullets
        self.aliens.empty()
        self.bullets.empty()

        # Create a new fleet and center the ship
        self._create_fleet()
        self.ship.center_ship()

    def _update_objects(self):
        """Update the ship, bullets, and aliens if the game is active."""
        if self.stats.game_active:
            self._update_ship()
            self._update_bullets()
            self._handle_bullet_alien_collisions()
            self._update_aliens()
            self._handle_ship_alien_collisions()
        else:
            # If the game is inactive, clear the aliens and bullets
            self.aliens.empty()
            self.bullets.empty()

    def _start_new_level(self):
        """Start a new level."""
        # Destroy existing bullets and create new fleet
        self.bullets.empty()
        self._create_fleet()
        self.settings.increase_speed()
        self.settings.increase_point_values()

        # Increase level
        self.stats.level += 1
        self.sb.prep_level()

    def _update_screen(self):
        """Update images on the screen, and flip to the new screen."""
        self.screen.fill(self.settings.bg_color)
        for bullet in self.bullets.sprites():
            bullet.draw_bullet()
        self.ship.blitme()
        self.aliens.draw(
            self.screen
        )  # calls the draw method for each alien in the group

        # Draw the score information
        self.sb.show_score()
        self.sb.show_high_score()
        self.sb.show_level()
        self.sb.show_ships()

        # Draw the play button if the game is inactive
        if not self.stats.game_active:
            self.play_button.draw_button()

        pygame.display.flip()  # make the most recently drawn screen visible


if __name__ == "__main__":
    ai = AlienInvasion()
    ai.run_game()
