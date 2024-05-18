from enum import Enum
import random

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


class Bullet:
    def __init__(self, position, normalized_velocity):
        self.life_counter = 120  # in frames
        self.sprite = self.init_sprite()
        self.position = position
        self.rect = self.sprite.get_rect(center=self.position)
        self.normalized_velocity = normalized_velocity
        self.speed = 10

    def init_sprite(self):
        size = 5
        surface = pygame.Surface((size, size))
        color = (192, 0, 0)
        pygame.draw.circle(surface, color, (size / 2, size / 2), size // 2)
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
    def __init__(self, position=None):
        self.sprite = self.init_sprite()
        if position is not None:
            self.position = position
        else:
            self.position = self.get_random_position()
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

    def get_random_position(self):
        position = (
            random.random() * DISPLAY_PARAMS.width - 1,
            random.random() * DISPLAY_PARAMS.height - 1,
        )
        return pygame.Vector2(position)

    def init_sprite(self):
        size = int(random.uniform(15, 60))
        surface = pygame.Surface((size, size))
        color = (255, 255, 255)
        pygame.draw.circle(surface, color, (size / 2, size / 2), size // 2, width=1)
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
        # self.position = pygame.Vector2(position)
        self.sprite = self.init_sprite()
        self.rect = self.sprite.get_rect(center=position)
        # self.rect = self.sprite.get_rect(topleft=position)
        self.orientation = 0
        self.normalized_velocity = pygame.Vector2(0, -1)
        self.speed = 0

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
        return surface

    def get_new_bullet_params(self):
        normalized_velocity = pygame.Vector2(0, -1).rotate(-self.orientation)
        position = self.rect.center + normalized_velocity * 50
        return position, normalized_velocity

    def update_orientation(self, rotation_direction):
        angular_velocity = 5
        self.orientation = (self.orientation + (rotation_direction * angular_velocity)) % 360

    def update_position(self, is_accelerating):
        max_speed = 8
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

    def wrap_coordinates(self, point):
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

    def draw(self, screen):
        rotated = pygame.transform.rotate(self.sprite, self.orientation)
        self.rect = rotated.get_rect(center=self.rect.center)
        screen.blit(rotated, self.rect)


class Game:
    BULLET_COOLDOWN_MS = 300

    def __init__(self):
        pygame.init()
        self.game_state = GameState.STARTING
        pygame.display.set_caption('jetblack')
        self.screen = pygame.display.set_mode((DISPLAY_PARAMS.width, DISPLAY_PARAMS.height))
        self.clock = pygame.time.Clock()
        self.player = PlayerSpaceship(pygame.Vector2(DISPLAY_PARAMS.width, DISPLAY_PARAMS.height) / 2)
        self.asteroids = [Asteroid() for _ in range(5)]
        self.bullets = []
        self.last_bullet_time = -1

    def get_rotation_direction(self, pressed_keys):
        if pressed_keys[pygame.K_a]:
            return 1  # counter-clockwise
        elif pressed_keys[pygame.K_d]:
            return -1
        else:
            return 0

    def draw_frame(self):
        self.screen.fill(DISPLAY_PARAMS.bg_color)
        # pygame.draw.line(self.screen, (255, 0, 0),
        #                  (0, DISPLAY_PARAMS.height / 2), (DISPLAY_PARAMS.width - 1, DISPLAY_PARAMS.height / 2))
        # pygame.draw.line(self.screen, (255, 0, 0),
        #                  (DISPLAY_PARAMS.width / 2, 0), (DISPLAY_PARAMS.width / 2, DISPLAY_PARAMS.height - 1))
        for asteroid in self.asteroids:
            asteroid.draw(self.screen)
        self.player.draw(self.screen)
        for bullet in self.bullets:
            bullet.draw(self.screen)

    def check_bullet_collisions(self):
        collided_asteroids = set()
        collided_bullets = set()
        for i, asteroid in enumerate(self.asteroids):
            for j, bullet in enumerate(self.bullets):
                if asteroid.rect.colliderect(bullet.rect):
                    collided_asteroids.add(i)
                    collided_bullets.add(j)
        self.asteroids = [
            asteroid
            for i, asteroid in enumerate(self.asteroids) if i not in collided_asteroids
        ]
        self.bullets = [
            bullet
            for j, bullet in enumerate(self.bullets) if j not in collided_bullets
        ]

    def check_player_collision(self):
        for asteroid in self.asteroids:
            if asteroid.rect.colliderect(self.player.rect):
                return True
        return False

    def show_game_over(self):
        font = pygame.font.Font(pygame.font.get_default_font(), 36)
        lines = [
            'GAME OVER...',
        ]
        for i, line in enumerate(lines):
            text_surface = font.render(
                line,
                True,
                (255, 0, 0),
                (0, 0, 0)
            )
            text_rect = text_surface.get_rect(
                center=(
                    DISPLAY_PARAMS.width // 2,
                    DISPLAY_PARAMS.height // 2
                )
            )
            self.screen.blit(text_surface, text_rect)

    def game_loop(self):
        rotation_direction = 0
        is_accelerating = False
        is_shooting = False
        ticks = pygame.time.get_ticks()
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (
                    event.type == pygame.KEYDOWN and pygame.key.get_pressed()[pygame.K_q]):
                pygame.quit()
                self.game_state = GameState.EXITED
                return

        rotation_direction = self.get_rotation_direction(pygame.key.get_pressed())
        is_accelerating = pygame.key.get_pressed()[pygame.K_w]
        if ticks - self.last_bullet_time >= self.BULLET_COOLDOWN_MS:
            is_shooting = pygame.key.get_pressed()[pygame.K_SPACE]
            if is_shooting:
                self.last_bullet_time = ticks

        if self.game_state == GameState.STARTING:
            self.draw_frame()
            self.game_state = GameState.RUNNING
        elif self.game_state == GameState.RUNNING:
            if is_shooting:
                self.bullets.append(Bullet(*self.player.get_new_bullet_params()))
            self.player.update_orientation(rotation_direction)
            self.player.update_position(is_accelerating)
            self.bullets = [bullet for bullet in self.bullets if not bullet.is_exhausted()]
            self.check_bullet_collisions()
            for bullet in self.bullets:
                bullet.update_position()
            for asteroid in self.asteroids:
                asteroid.update_position()
            self.draw_frame()
            if self.check_player_collision():
                self.game_state = GameState.GAME_OVER
        if self.game_state == GameState.GAME_OVER:
            self.show_game_over()
        pygame.display.set_caption(f'jetblack (FPS: {self.clock.get_fps():.2f})')
        pygame.display.update()
        self.clock.tick(DISPLAY_PARAMS.max_fps)

    def run(self):
        while not self.game_state == GameState.EXITED:
            self.game_loop()


if __name__ == '__main__':
    game = Game()
    game.run()
