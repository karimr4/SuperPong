import math
import random
import asyncio
import pygame

pygame.init()

# ==========================================
# UNIT 2 MATH & AI EXPLANATION
# ==========================================
# Vectors: Used for the player, balls, rockets, and projectiles store positions as Vector2 objects.
# Distance: Rockets measure their distance from the player to decide when to attack.
# Normalization: Rockets and projectiles normalize direction and is used for directional movement. 
# Angles(sin and cosine): Used primarly for the rockets and their rotations and where they are facing.
# Velocity and acceleration: Rockets change velocity using acceleration before moving like the asteroids game.
# Dot product: A rocket checks whether the player is in front of it before attacking and to help decide when or not go go off or on patrol and attack.
# AI decisions: Rockets patrol when they cannot see the player and chase/fire when the player is close and in front. They change states from patrl to attack and vice versa. 

screen_width = 800
screen_height = 600
fps = 60

game_background = (15, 15, 30)
text_color = (240, 240, 255)
platform_color = (0, 255, 150)

ball_color = (255, 215, 0)

projectile_color = (255, 100, 0)
patrol_color = (240, 240, 240)
attack_color = (255, 50, 50)

screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("SuperPong")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 22)
large_font = pygame.font.SysFont("Arial", 48)


class PlayerPlatform:
    def __init__(self):
        self.width = 120
        self.height = 15
        self.position = pygame.Vector2(screen_width // 2, screen_height - 40)
        self.speed = 8
        self.lives = 3
        self.shield_max = 100
        self.shield_value = 100
        self.shield_active = False

    def update(self):
        keys = pygame.key.get_pressed()

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.position.x -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.position.x += self.speed

        # makes sure the platform doesn't go off the screen and noclip
        self.position.x = max(self.width / 2, min(screen_width - self.width / 2, self.position.x))

        if keys[pygame.K_SPACE] and self.shield_value > 0:
            self.shield_active = True
            self.shield_value = max(0, self.shield_value - 0.5)
        else:
            self.shield_active = False

        if self.shield_value == 0:
            self.shield_active = False

    def draw(self, surface):
        platform = pygame.Rect(
            int(self.position.x - self.width / 2),
            int(self.position.y - self.height / 2),
            self.width,
            self.height
        )
        pygame.draw.rect(surface, platform_color, platform)

        if self.shield_active:
            shield_surface = pygame.Surface((self.width * 2, self.width * 2), pygame.SRCALPHA)
            pygame.draw.circle(
                shield_surface,
                (0, 191, 255, 120),
                (self.width, self.width),
                self.width // 2 + 15,
                3
            )
            surface.blit(
                shield_surface,
                (int(self.position.x - self.width), int(self.position.y - self.width))
            )


class Ball:
    def __init__(self):
        self.position = pygame.Vector2(screen_width // 2, screen_height // 3)
        self.velocity = pygame.Vector2(random.choice([-4, 4]), -4)
        self.radius = 8

    def update(self):
        self.position += self.velocity

        if self.position.x <= self.radius:
            self.position.x = self.radius
            self.velocity.x *= -1
        elif self.position.x >= screen_width - self.radius:
            self.position.x = screen_width - self.radius
            self.velocity.x *= -1

        if self.position.y <= self.radius:
            self.position.y = self.radius
            self.velocity.y *= -1

    def draw(self, surface):
        pygame.draw.circle(
            surface,
            ball_color,
            (int(self.position.x), int(self.position.y)),
            self.radius
        )


class RocketEnemy:
    def __init__(self):
        self.position = pygame.Vector2(
            random.randint(50, screen_width - 50),
            random.randint(50, int(screen_height * 0.6))
        )
        self.velocity = pygame.Vector2(random.choice([-2, 2]), random.choice([-1, 1]))
        self.acceleration = pygame.Vector2(0, 0)
        self.angle = random.randint(0, 360)
        self.max_speed = 3
        self.state = "patrol"
        self.shoot_cooldown = 0
        self.shoot_delay = 45

    def update(self, player_position):
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

        distance = self.position.distance_to(player_position)
        # vector use 
        # this forward vector points in the direction the rocket is facing
        radians = math.radians(self.angle)
        forward = pygame.Vector2(math.cos(radians), -math.sin(radians))

        # I used normalization here so that the dot product is gong to compare direction instead of the distance to the player
        to_player = player_position - self.position
        if to_player.length() > 0:
            to_player = to_player.normalize()
        else:
            to_player = pygame.Vector2(0, 0)

        dot_product = forward.dot(to_player)
        detection_range = 450
        fov_threshold = 0.5
        # dot product 
        #Used dot product and detection range (distance) to determine wheter or not the player meets the requirments to be attacked
        if distance < detection_range and dot_product > fov_threshold:
            self.state = "attack"
            self.acceleration = to_player * 0.1
        else:
            self.state = "patrol"
            self.acceleration = pygame.Vector2(
                random.uniform(-0.05, 0.05),
                random.uniform(-0.05, 0.05)
            )
            self.angle += random.choice([-2, 0, 2])
        # veloctity and acceleration
        #this statisfies the accleration and velocty requirement, velocity changes the position and acceleration is what changes velocity
        self.velocity += self.acceleration
        if self.velocity.length() > self.max_speed:
            self.velocity.scale_to_length(self.max_speed)
        self.position += self.velocity

        patrol_limit_y = int(screen_height * 0.8)
        if self.position.x < 20:
            self.position.x = 20
            self.velocity.x = abs(self.velocity.x)
        elif self.position.x > screen_width - 20:
            self.position.x = screen_width - 20
            self.velocity.x = -abs(self.velocity.x)

        if self.position.y < 20:
            self.position.y = 20
            self.velocity.y = abs(self.velocity.y)
        elif self.position.y > patrol_limit_y:
            self.position.y = patrol_limit_y
            self.velocity.y = -abs(self.velocity.y)

        if self.velocity.length() > 0:
            movement_direction = self.velocity.normalize()
            self.angle = math.degrees(math.atan2(-movement_direction.y, movement_direction.x))

    def should_fire(self):
        if self.state == "attack" and self.shoot_cooldown == 0:
            self.shoot_cooldown = self.shoot_delay
            return True
        return False
    # rotation
    # this uses the trig stuff like cos, sin as it draws the rotating rocket ship based on the direction its facing and position 
    def draw(self, surface):
        radians = math.radians(self.angle)
        tip = self.position + pygame.Vector2(math.cos(radians), -math.sin(radians)) * 18
        left_tail = self.position + pygame.Vector2(
            math.cos(radians + math.radians(140)),
            -math.sin(radians + math.radians(140))
        ) * 12
        right_tail = self.position + pygame.Vector2(
            math.cos(radians - math.radians(140)),
            -math.sin(radians - math.radians(140))
        ) * 12

        color = attack_color if self.state == "attack" else patrol_color
        pygame.draw.polygon(surface, color, [tip, left_tail, right_tail])


class Projectile:
    def __init__(self, start_position, target_position):
        self.position = pygame.Vector2(start_position)
        self.radius = 4
        self.speed = 6
            # normalziation 
        # for here, normalizing makes every projectile travel at the same speed toward its target
        #the projectiles are the bullets that the rockets shoot at the platform 
        direction = target_position - start_position
        if direction.length() > 0:
            direction = direction.normalize()
        else:
            direction = pygame.Vector2(0, 1)

        self.velocity = direction * self.speed

    def update(self):
        self.position += self.velocity

    def draw(self, surface):
        pygame.draw.circle(
            surface,
            projectile_color,
            (int(self.position.x), int(self.position.y)),
            self.radius
        )


def reset_game():
    player = PlayerPlatform()
    balls = [Ball()]
    rockets = [RocketEnemy()]
    projectiles = []
    score = 0
    spawn_timer = 0
    return player, balls, rockets, projectiles, score, spawn_timer


async def main():
    player, balls, rockets, projectiles, score, spawn_timer = reset_game()
    game_over = False

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

            if event.type == pygame.KEYDOWN and game_over and event.key == pygame.K_r:
                player, balls, rockets, projectiles, score, spawn_timer = reset_game()
                game_over = False

        if not game_over:
            spawn_timer += 1
            if spawn_timer >= 900:
                spawn_timer = 0
                balls.append(Ball())
                rockets.append(RocketEnemy())

            player.update()

            for ball in balls:
                ball.update()

            for rocket in rockets:
                rocket.update(player.position)
                if rocket.should_fire():
                    projectiles.append(Projectile(rocket.position, player.position))

            for projectile in projectiles:
                projectile.update()

            projectiles = [
                projectile for projectile in projectiles
                if 0 <= projectile.position.x<= screen_width
                and 0 <= projectile.position.y <=screen_height
            ]

            #When the ball hits the platform, it checks if the platform and it made contact and bounces uo
        # this is also how you get more sheild energy thing and increses score so you don't run out of sheid 
            for ball in balls:
                ball_bottom = ball.position.y+ ball.radius
                platform_top = player.position.y -player.height /2
                platform_bottom = player.position.y +player.height/2
                platform_left = player.position.x -player.width /2
                platform_right = player.position.x + player.width /2

                if (platform_top <= ball_bottom <= platform_bottom
                        and platform_left <= ball.position.x <= platform_right
                        and ball.velocity.y > 0):
                    ball.velocity.y = -abs(ball.velocity.y)
                    score += 1
                    player.shield_value = min(player.shield_max, player.shield_value + 15)

            balls = [ball for ball in balls if ball.position.y < screen_height + 20]
            if not balls:
                game_over = True

            remaining_projectiles = []
            for projectile in projectiles:
                distance_to_player =projectile.position.distance_to(player.position)
                hit_platform = (
                    player.position.y - player.height / 2 <= projectile.position.y
                    <= player.position.y + player.height/2
                    and player.position.x - player.width / 2<= projectile.position.x
                    <= player.position.x + player.width / 2
                )

                if hit_platform or distance_to_player < 20:
                    if not player.shield_active:
                        player.lives -= 1
                        if player.lives <= 0:
                            game_over = True
                    continue

                remaining_projectiles.append(projectile)
            projectiles = remaining_projectiles

        screen.fill(game_background)
        player.draw(screen)

        for ball in balls:
            ball.draw(screen)
        for rocket in rockets:
            rocket.draw(screen)
        for projectile in projectiles:
            projectile.draw(screen)

        score_text = font.render(f"Score: {score}", True,text_color)
        lives_text = font.render(f"Lives: {player.lives}",True, text_color)
        balls_text = font.render(f"Active Balls: {len(balls)}", True,text_color)
        shield_text = font.render(
            f"Shield Energy: {int(player.shield_value)}%",
            True,
            platform_color if player.shield_active else text_color
        )
        instructions = font.render(
            "A/D or Arrows: Move | Hold space,: Shield",
            True,
            (160, 160, 180)
        )

        screen.blit(score_text,(20, 20))
        screen.blit(lives_text,(20, 50))
        screen.blit(balls_text, (20, 80))
        screen.blit(shield_text, (screen_width - 250, 20))
        screen.blit(instructions,(20, screen_height - 30))

        if game_over:
            over_text = large_font.render("GAME OVER", True, (255, 50, 50))
            over_rect = over_text.get_rect(center=(screen_width // 2,screen_height // 2- 35))
            restart_text = font.render("Press R to restart", True, text_color)
            restart_rect = restart_text.get_rect(center=(screen_width// 2, screen_height // 2 +20))
            screen.blit(over_text, over_rect)
            screen.blit(restart_text, restart_rect)

        pygame.display.flip()
        clock.tick(fps)
        await asyncio.sleep(0)
        
if __name__ == "__main__":
    asyncio.run(main())