from enum import Enum
import random
import math
from pathlib import Path

import pygame


class DISPLAY_PARAMS:
    width = 1600
    height = 900
    max_fps = 60
    bg_color = (0, 0, 0)
    # bg_color = (30, 30, 30)


class GameState(Enum):
    STARTING = 1
    RUNNING = 2
    GAME_OVER = 3
    EXITED = 4
    RESTARTING = 5


def wrap_coordinates(point):
    x, y = point
    if x < 0:
        x = DISPLAY_PARAMS.width + x
    elif x >= DISPLAY_PARAMS.width:
        x = x - DISPLAY_PARAMS.width
    if y < 0:
        y = DISPLAY_PARAMS.height + y
    elif y >= DISPLAY_PARAMS.height:
        y = y - DISPLAY_PARAMS.height
    return pygame.Vector2(x, y)


def get_random_position():
    position = (
        random.random() * DISPLAY_PARAMS.width - 1,
        random.random() * DISPLAY_PARAMS.height - 1,
    )
    return pygame.Vector2(position)


def get_random_velocity():
    normalized_velocity = pygame.Vector2(
        2 * random.random() - 1,
        2 * random.random() - 1
    ).normalize()
    return normalized_velocity


class SoundMixer:
    def __init__(self):
        pygame.mixer.init()
        self.samples = self.init_samples()

    def init_samples(self):
        samples = dict()
        samples['shooting'] = pygame.mixer.Sound(Path('sounds') / 'shooting_1.wav')
        samples['explosion_small'] = pygame.mixer.Sound(Path('sounds') / 'explosion_1.wav')
        samples['explosion_large'] = pygame.mixer.Sound(Path('sounds') / 'explosion_2.wav')
        return samples

    def play_shooting(self):
        self.samples['shooting'].play()

    def play_explosion(self, size=None):
        if size is None or size < 40:
            self.samples['explosion_small'].play()
        else:
            self.samples['explosion_large'].play()


class Scoreboard:
    def __init__(self, position):
        self.font = pygame.font.Font(pygame.font.get_default_font(), 48)
        self.position = position
        self.score = 0

    def get_score(self):
        return self.score

    def increment_score(self, delta=1):
        self.score += delta

    def draw(self, screen):
        text_surface = self.font.render(f'{self.score}', True, (192, 0, 0))
        screen.blit(text_surface, self.position)


class Bullet:
    def __init__(self, position, normalized_velocity, color=(0, 192, 0), size=5, speed=10):
        self.life_counter = 120  # in frames
        self.color = color
        self.size = size
        self.speed = speed
        self.sprite = self.init_sprite()
        self.position = position
        self.rect = self.sprite.get_rect(center=self.position)
        self.normalized_velocity = normalized_velocity

    def init_sprite(self):
        size = self.size
        surface = pygame.Surface((size, size))
        pygame.draw.circle(surface, self.color, (size / 2, size / 2), size // 2)
        return surface

    def update_position(self):
        position = self.position + self.normalized_velocity * self.speed
        position = wrap_coordinates(position)
        self.position = position
        self.rect.center = position

    def draw(self, screen):
        screen.blit(self.sprite, self.rect)

    def is_exhausted(self):
        self.life_counter -= 1
        if self.life_counter <= 0:
            return True
        else:
            return False


class Asteroid:
    def __init__(self, position=None, size=None):
        if position is not None:
            self.position = position
        else:
            self.position = get_random_position()
        self.size = size
        self.sprite = self.init_sprite()
        self.rect = self.sprite.get_rect(center=self.position)
        self.normalized_velocity = self.get_random_velocity()
        self.speed = random.random() * 4.5 + 0.5
        # print(self.normalized_velocity, self.speed)

    def get_random_velocity(self):
        velocity = (
            2 * random.random() - 1,
            2 * random.random() - 1,
        )
        velocity = pygame.Vector2(velocity).normalize()
        return velocity

    def get_random_polygon(self, min_radius, max_radius, min_points=7, max_points=16, angle_step=5):
        num_points = random.randint(min_points, max_points)
        angles = sorted(random.sample(range(0, 360, angle_step), num_points))
        points = []
        for angle in angles:
            radius = random.uniform(min_radius, max_radius)
            x = math.cos(math.radians(angle)) * radius + max_radius
            y = math.sin(math.radians(angle)) * radius + max_radius
            points.append((x, y))
        min_x = min(p[0] for p in points)
        min_y = min(p[1] for p in points)
        points = [(p[0] - min_x, p[1] - min_y) for p in points]
        return points

    def init_sprite(self):
        if self.size is None:
            self.size = int(random.uniform(15, 90))
        radius = self.size / 2
        points = self.get_random_polygon(radius * 0.9, radius - 1)
        max_x = max(p[0] for p in points)
        max_y = max(p[1] for p in points)
        surface = pygame.Surface((int(max_x + 1), int(max_y + 1)))  # adjust bounding rect
        self.size = max(max_x, max_y)
        color = (255, 255, 255)
        pygame.draw.polygon(surface, color, points, width=1)
        surface.set_colorkey((0, 0, 0))
        return surface

    def update_position(self):
        position = self.position + self.normalized_velocity * self.speed
        position = wrap_coordinates(position)
        self.position = position
        self.rect.center = position

    def draw(self, screen):
        screen.blit(self.sprite, self.rect)


class PlayerSpaceship:
    def __init__(self, position):
        self.sprite = self.init_sprite()
        self.rect = self.sprite.get_rect(center=position)
        self.orientation = 0
        self.normalized_velocity = pygame.Vector2(0, -1)
        self.speed = 0
        self.is_dead = False

    def init_sprite(self):
        w, h = 30, 45
        surface = pygame.Surface((w, h))
        color = (255, 255, 255)
        triangle_points = [
            (w / 2, 0),
            (0, h - 1),
            (w - 1, h - 1)
        ]
        pygame.draw.polygon(surface, color, triangle_points, width=1)
        surface.set_colorkey((0, 0, 0))
        return surface

    def get_position(self):
        return self.rect.center

    def get_new_bullet_params(self):
        normalized_velocity = pygame.Vector2(0, -1).rotate(-self.orientation)
        position = self.rect.center + normalized_velocity * 50
        return position, normalized_velocity

    def update_orientation(self, rotation_direction):
        angular_velocity = 4.5
        self.orientation = (self.orientation + (rotation_direction * angular_velocity)) % 360

    def update_position(self, is_accelerating):
        max_speed = 7
        if is_accelerating:
            a = pygame.Vector2(0, -1).rotate(-self.orientation)
        else:
            a = (0, 0)
        velocity = (self.normalized_velocity * self.speed) + a
        self.speed = min(velocity.magnitude(), max_speed)
        if self.speed > 0:
            self.normalized_velocity = velocity.normalize()
        self.rect.center = (self.rect.center + self.normalized_velocity * self.speed)
        self.rect.center = wrap_coordinates(self.rect.center)

    def draw(self, screen):
        rotated = pygame.transform.rotate(self.sprite, self.orientation)
        self.rect = rotated.get_rect(center=self.rect.center)
        screen.blit(rotated, self.rect)


class Debris:
    SPEED = 1
    ROTATION_SPEED = 1

    def __init__(self, initial_position, num_pieces=6, size=20):
        self.num_pieces = num_pieces
        self.initial_position = pygame.Vector2(initial_position)
        self.pieces = self.generate_pieces()
        self.size = size

    def generate_pieces(self):
        pieces = []
        for _ in range(self.num_pieces):
            orientation = random.random() * 360
            velocity = pygame.Vector2(0, -1).rotate(-random.random() * 360)
            pieces.append(dict(position=self.initial_position, orientation=orientation, velocity=velocity))
        return pieces

    def update(self):
        for piece in self.pieces:
            piece['position'] = piece['position'] + piece['velocity'] * self.SPEED
            piece['orientation'] = (piece['orientation'] + self.ROTATION_SPEED) % 360

    def draw(self, screen):
        for piece in self.pieces:
            segment = pygame.Vector2(0, -1).rotate(-piece['orientation']) * self.size / 2
            pygame.draw.line(screen, (255, 255, 255), piece['position'] + segment, piece['position'] - segment)


class EnemySaucer:
    def __init__(self, position):
        self.sprite = self.init_sprite()
        self.position = position
        self.rect = self.sprite.get_rect(center=position)
        self.normalized_velocity = pygame.Vector2(1, 0)
        self.speed = 3

    def init_sprite(self):
        w, h = 60, 30
        surface = pygame.Surface((w, h))
        color = (192, 0, 0)
        bottom_points = [
            (0, (2 / 3) * h),
            (0.15 * w, h - 1),
            (w - 1 - 0.15 * w, h - 1),
            (w - 1, (2 / 3) * h),
            (0, (2 / 3) * h),
        ]
        middle_points = [
            (0, (2 / 3) * h),
            (0.3 * w, (1 / 3) * h),
            (w - 1 - 0.3 * w, (1 / 3) * h),
            (w - 1, (2 / 3) * h),
        ]
        top_points = [
            (0.3 * w, (1 / 3) * h),
            (0.4 * w, 0),
            (w - 1 - 0.4 * w, 0),
            (w - 1 - 0.3 * w, (1 / 3) * h),
        ]
        pygame.draw.polygon(surface, color, bottom_points, width=1)
        pygame.draw.polygon(surface, color, middle_points, width=1)
        pygame.draw.polygon(surface, color, top_points, width=1)
        surface.set_colorkey((0, 0, 0))
        return surface

    def get_position(self):
        return self.rect.center

    def maybe_shoot(self, target_position):
        if random.random() > 0.01:
            return None
        position = pygame.Vector2(self.rect.center)
        normalized_velocity = (target_position - position).normalize()
        return position, normalized_velocity

    def get_new_bullet_params(self):
        normalized_velocity = get_random_velocity()
        position = self.rect.center + normalized_velocity * 50
        return position, normalized_velocity

    def update_position(self):
        if random.random() < 0.015:  # randomly change direction
            self.normalized_velocity = get_random_velocity()
        position = self.position + self.normalized_velocity * self.speed
        position = wrap_coordinates(position)
        self.position = position
        self.rect.center = position

    def draw(self, screen):
        self.rect = self.sprite.get_rect(center=self.rect.center)
        screen.blit(self.sprite, self.rect)


class Game:
    BULLET_COOLDOWN_MS = 300
    SAUCER_RESPAWN_COOLDOWN_MS = 15000
    NUM_SPAWNED_ASTEROIDS = 9

    def __init__(self):
        pygame.init()
        self.game_state = GameState.STARTING
        pygame.display.set_caption('jetblack')
        self.screen = pygame.display.set_mode((DISPLAY_PARAMS.width, DISPLAY_PARAMS.height))
        self.sound_mixer = SoundMixer()
        self.clock = pygame.time.Clock()
        self.scoreboard = Scoreboard((10, 10))
        self.player = PlayerSpaceship(pygame.Vector2(DISPLAY_PARAMS.width, DISPLAY_PARAMS.height) / 2)
        self.debris = None
        self.player_bullets = []
        self.last_bullet_time = -1
        self.asteroids = self.spawn_asteroids(self.NUM_SPAWNED_ASTEROIDS)
        self.saucer = None
        self.last_saucer_death_time = pygame.time.get_ticks()
        self.saucer_bullets = []

    def spawn_asteroids(self, num_asteroids):
        positions = self.get_valid_spawn_positions(num_asteroids)
        return [Asteroid(position) for position in positions]

    def get_valid_spawn_positions(self, num_positions, min_distance=200):
        new_positions = []
        tabu_positions = [pygame.Vector2(self.player.get_position())]
        while len(new_positions) < num_positions:
            candidate_pos = get_random_position()
            if all(candidate_pos.distance_to(tabu_pos) >= min_distance for tabu_pos in tabu_positions):
                tabu_positions.append(candidate_pos)
                new_positions.append(candidate_pos)
        return new_positions

    def get_rotation_direction(self, pressed_keys):
        if pressed_keys[pygame.K_a]:
            return 1  # counter-clockwise
        elif pressed_keys[pygame.K_d]:
            return -1
        else:
            return 0

    def draw_frame(self):
        self.screen.fill(DISPLAY_PARAMS.bg_color)
        for asteroid in self.asteroids:
            asteroid.draw(self.screen)
        if self.saucer is not None:
            self.saucer.draw(self.screen)
        if not self.player.is_dead:
            self.player.draw(self.screen)
        if self.debris is not None:
            self.debris.draw(self.screen)
        for bullet in self.player_bullets:
            bullet.draw(self.screen)
        for bullet in self.saucer_bullets:
            bullet.draw(self.screen)
        self.scoreboard.draw(self.screen)

    def check_player_bullet_collisions(self) -> tuple[int, bool]:
        is_saucer_collided = False
        destroyed_asteroid_sizes = []
        collided_asteroids = set()
        collided_bullets = set()
        new_asteroids = []
        for i, bullet in enumerate(self.player_bullets):
            if self.saucer is not None and self.saucer.rect.colliderect(bullet.rect):
                collided_bullets.add(i)
                is_saucer_collided = True
                continue
            for j, asteroid in enumerate(self.asteroids):
                if asteroid.rect.colliderect(bullet.rect):
                    destroyed_asteroid_sizes.append(asteroid.size)
                    collided_asteroids.add(j)
                    collided_bullets.add(i)
                    if asteroid.size > 40:
                        new_asteroids.extend(
                            [
                                Asteroid(position=asteroid.position, size=asteroid.size * 0.65)
                                for _ in range(2)
                            ]
                        )
        self.asteroids = [
            asteroid
            for i, asteroid in enumerate(self.asteroids) if i not in collided_asteroids
        ]
        self.player_bullets = [
            bullet
            for j, bullet in enumerate(self.player_bullets) if j not in collided_bullets
        ]
        self.asteroids.extend(new_asteroids)
        return destroyed_asteroid_sizes, is_saucer_collided

    def check_player_collision(self):
        smaller_rect = self.player.rect.copy().scale_by(0.5)
        for asteroid in self.asteroids:
            if asteroid.rect.colliderect(smaller_rect):
                return True
        for bullet in self.saucer_bullets:
            if bullet.rect.colliderect(smaller_rect):
                return True
        if self.saucer is not None and self.saucer.rect.colliderect(smaller_rect):
            return True
        return False

    def show_game_over(self):
        font_size = 32
        font = pygame.font.Font(pygame.font.get_default_font(), font_size)
        lines = [
            'GAME OVER...',
            '(press R to restart)'
        ]
        for i, line in enumerate(lines):
            text_surface = font.render(
                line,
                True,
                (255, 0, 0),
            )
            text_rect = text_surface.get_rect(
                center=(
                    DISPLAY_PARAMS.width // 2,
                    DISPLAY_PARAMS.height // 2 + font_size * (i - 1)
                )
            )
            self.screen.blit(text_surface, text_rect)

    def _generate_bullets(self, is_shooting):
        if is_shooting:
            self.player_bullets.append(Bullet(*self.player.get_new_bullet_params()))
            self.sound_mixer.play_shooting()
        self.player_bullets = [bullet for bullet in self.player_bullets if not bullet.is_exhausted()]

        if self.saucer is not None:
            bullet_params = self.saucer.maybe_shoot(self.player.get_position())
            if bullet_params is not None:
                self.saucer_bullets.append(Bullet(*bullet_params, color=(192, 0, 0), speed=6))
        self.saucer_bullets = [bullet for bullet in self.saucer_bullets if not bullet.is_exhausted()]

    def _update_positions(self, is_accelerating, rotation_direction):
        self.player.update_orientation(rotation_direction)
        self.player.update_position(is_accelerating)
        if self.saucer is not None:
            self.saucer.update_position()
        for bullet in self.player_bullets + self.saucer_bullets:
            bullet.update_position()
        for asteroid in self.asteroids:
            asteroid.update_position()

    def _process_collisions(self, ticks):
        destroyed_asteroid_sizes, is_saucer_collided = self.check_player_bullet_collisions()
        self.scoreboard.increment_score(len(destroyed_asteroid_sizes) + 10 * is_saucer_collided)
        if destroyed_asteroid_sizes:
            self.sound_mixer.play_explosion(max(size for size in destroyed_asteroid_sizes))
        if is_saucer_collided:
            self.saucer = None
            self.sound_mixer.play_explosion()
            self.last_saucer_death_time = ticks
        is_player_collided = self.check_player_collision()
        if is_player_collided:
            self.sound_mixer.play_explosion()
            self.player.is_dead = True
            self.debris = Debris(self.player.get_position())

    def _spawn(self, ticks):
        if not self.asteroids:
            self.asteroids = self.spawn_asteroids(self.NUM_SPAWNED_ASTEROIDS)
        if self.saucer is None and ticks - self.last_saucer_death_time > self.SAUCER_RESPAWN_COOLDOWN_MS:
            self.saucer = EnemySaucer(self.get_valid_spawn_positions(1)[0])

    def game_loop(self):
        rotation_direction = 0
        is_accelerating = False
        is_shooting = False
        ticks = pygame.time.get_ticks()
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (
                    event.type == pygame.KEYDOWN and pygame.key.get_pressed()[pygame.K_ESCAPE]):
                self.game_state = GameState.EXITED
                return

        rotation_direction = self.get_rotation_direction(pygame.key.get_pressed())
        is_accelerating = pygame.key.get_pressed()[pygame.K_w]
        if ticks - self.last_bullet_time > self.BULLET_COOLDOWN_MS:
            is_shooting = pygame.key.get_pressed()[pygame.K_SPACE]
            if is_shooting:
                self.last_bullet_time = ticks
        if self.game_state == GameState.STARTING:
            self.draw_frame()
            self.game_state = GameState.RUNNING
        elif self.game_state == GameState.RUNNING:
            self._generate_bullets(is_shooting)
            self._update_positions(is_accelerating, rotation_direction)
            self._process_collisions(ticks)
            self.draw_frame()
            if self.player.is_dead:
                self.game_state = GameState.GAME_OVER
            else:
                self._spawn(ticks)
        if self.game_state == GameState.GAME_OVER:
            self.debris.update()
            self.draw_frame()
            self.show_game_over()
            if pygame.key.get_pressed()[pygame.K_r]:
                self.game_state = GameState.RESTARTING
        pygame.display.set_caption(f'jetblack (FPS: {self.clock.get_fps():.2f})')
        pygame.display.update()
        self.clock.tick(DISPLAY_PARAMS.max_fps)

    def run(self):
        while self.game_state not in [GameState.EXITED, GameState.RESTARTING]:
            self.game_loop()
        if self.game_state == GameState.RESTARTING:
            return True
        else:
            return False


if __name__ == '__main__':
    while True:
        game = Game()
        restart = game.run()
        if not restart:
            break
