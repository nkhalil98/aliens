from pathlib import Path

HIGH_SCORE_PATH = Path(__file__).parent / "assets" / "score" / "high_score.txt"


class GameStats:
    """Track statistics for Alien Invasion."""

    def __init__(self, ai_game):
        """Initialize statistics."""
        self.settings = ai_game.settings
        self.init_stats()

        # Start Alien Invasion in an inactive state
        self.game_active = False

        # Get stored high score if possible or set to 0
        self.high_score = self.get_high_score()

    def init_stats(self):
        """Initialize dynamic statistics."""
        self.ships_left = self.settings.ship_limit
        self.score = 0
        self.level = 1

    def get_high_score(self):
        """Retrieve the high score from a file if it exists."""
        try:
            with open(HIGH_SCORE_PATH, "r") as file:
                high_score = int(file.read())
        except FileNotFoundError:
            high_score = 0

        return high_score

    def save_high_score(self):
        """Save the high score to a file."""
        with open(HIGH_SCORE_PATH, "w") as file:
            file.write(str(self.high_score))
