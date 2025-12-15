
import math
import random
import turtle

def wait_for_seconds(t):
    for i in range(0, int(t*16)):
        yield

def start_coroutine(coroutine):
    coroutines.append(coroutine)

def stop_coroutine(coroutine):
    coroutines.remove(coroutine)

class Component:
    def __init__(self):
        self.game_object = None

    def update(self):
        pass

    def start(self):
        pass

class Vector2:
    def __init__(self, x = 0, y = 0):
        self.x = x
        self.y = y

    def __add__(self, other):
        if isinstance(other, Vector2):
            return Vector2(self.x + other.x, self.y + other.y)
        else:
            return Vector2(self.x + other, self.y + other)

    def __sub__(self, other):
        if isinstance(other, Vector2):
            return Vector2(self.x - other.x, self.y - other.y)
        else:
            return Vector2(self.x - other, self.y - other)

    def __mul__(self, other):
        if isinstance(other, Vector2):
            return Vector2(self.x * other.x, self.y * other.y)
        else:
            return Vector2(self.x * other, self.y * other)

    def __truediv__(self, other):
        if isinstance(other, Vector2):
            return Vector2(self.x / other.x, self.y / other.y)
        return Vector2(self.x / other, self.y / other)

    def __eq__(self, other):
        if isinstance(other, Vector2):
            return (self.x == other.x and self.y == other.y)
        else:
            return None

    def magnitude(self):
        return (self.x**2 + self.y**2)**0.5

class Transform(Component):
    def __init__(self):
        super().__init__()
        self._parent = None
        self.children = []
        self.position = Vector2()
        self.rotation = 0
        self.scale = Vector2(1, 1)
        self.local_position = None
        self.local_scale = None
        self.local_rotation = None
        self.ignore_parent_scale = False

    def update(self):
        if self.parent is not None:
            self.position = self.parent.position + self.local_position
            self.rotation = self.parent.rotation + self.local_rotation
            if not self.ignore_parent_scale:
                self.scale = self.parent.scale * self.local_scale
            self.rotation = self.parent.rotation + self.local_rotation

    def tween_position(self, new_position, speed):
        return Lerp(self, "position", new_position, speed)

    def tween_rotation(self, new_rotation, speed):
        return Lerp(self, "rotation", new_rotation, speed)

    def tween_scale(self, new_scale, speed):
        return Lerp(self, "scale", new_scale, speed)

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, val: "Transform"):
        self._parent = val
        if val is not None:
            val.children.append(self)
            self.on_parent()
        else:
            self.on_unparent()


    @parent.deleter
    def parent(self):
        self._parent.children.remove(self)
        self._parent = None
        self.on_unparent()

    def on_parent(self):
        self.local_position = self.position
        self.local_scale = self.scale
        self.local_rotation = self.rotation

    def on_unparent(self):
        self.local_position = None
        self.local_scale = None
        self.local_rotation = None

class GameObject(Component):
    def __init__(self, position: Vector2 = None, scale: Vector2 = None, starting_comps = None):
        super().__init__()
        self.game_object = self
        self.components = []

        if position is None:
            position = Vector2()
        if scale is None:
            scale = Vector2(1, 1)
        if starting_comps is None:
            starting_comps = []

        self.transform = self.add_component(Transform())
        self.transform.position = position
        self.transform.scale = scale
        game_objects.append(self)

        for comp in starting_comps:
            self.add_component(comp)

    def destroy(self):
        if not (self in game_objects):
            return
        game_objects.remove(self)
        for comp in self.components:
            if isinstance(comp, RenderObject):
                comp.pen.clear()
                render_objects.remove(comp)
            if isinstance(comp, Bullet):
                bullets.remove(comp)
        for child in self.transform.children:
            child.game_object.destroy()

    def add_component(self, comp):
        self.components.append(comp)
        comp.game_object = self
        comp.start()
        return comp

    def remove_component(self, comp):
        self.components.remove(comp)

    def update(self):
        for comp in self.components:
            comp.update()


class RenderObject(Component):
    def __init__(self):
        super().__init__()
        self.pen = turtle.Turtle()
        self.pen.hideturtle()
        self.pen.penup()
        self.pen.speed(0)
        self.sort_order = 0
        self.visible = True
        render_objects.append(self)

    def toggle_visibility(self):
        if self.visible:
            self.visible = False
        else:
            self.visible = True

    def render(self):
        self.pen.clear()
        if self.visible:
            self.pen.shapesize(stretch_len=self.game_object.transform.scale.x, stretch_wid=self.game_object.transform.scale.y)
            self.pen.setheading(self.game_object.transform.rotation)
            self.pen.goto(self.game_object.transform.position.x, self.game_object.transform.position.y)
            self.pseudostamp()

    def pseudostamp(self):
        pass

class Sprite(RenderObject):
    def __init__(self, color = "white", shape = "square"):
        super().__init__()
        self.color = color
        self.shape = shape

    def pseudostamp(self):
        super().pseudostamp()
        self.pen.shape(self.shape)
        self.pen.color(self.color)
        self.pen.stamp()

class Text(RenderObject):
    def __init__(self, text = " ", color = "black", font_size = "54", font = "arial", align = "center"):
        self.text = text
        self.color = color
        self.font = font
        self.font_size = font_size
        self.align = align
        super().__init__()

    def pseudostamp(self):
        super().pseudostamp()
        self.pen.color(self.color)
        self.pen.write(self.text, font=(self.font, self.font_size), align=self.align)

class Input:
    def __init__(self):
        self.keys = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z",
                     "Up", "Down", "Left", "Right",
                     "space", "Return", "Shift_L",
                     "1", "2", "3", "4", "5", "6", "7", "8", "9", "0"]
        self.keys_down = set()
        self.keys_down_this_frame = set()
        self.keys_up_this_frame = set()

        screen.listen()
        for key in self.keys:
            screen.onkeypress(lambda k = key: self.internal_down(k), key)
            screen.onkeyrelease(lambda k = key: self.internal_up(k), key)

    def update(self):
        self.keys_down_this_frame.clear()
        self.keys_up_this_frame.clear()

    def internal_down(self, key):
        self.keys_down.add(key)
        self.keys_down_this_frame.add(key)

    def internal_up(self, key):
        self.keys_down.discard(key)
        self.keys_up_this_frame.add(key)

    def get_key(self, k):
        if k in self.keys_down:
            return True
        else:
            return False

    def get_key_down(self, k):
        if k in self.keys_down_this_frame:
            return True
        else:
            return False

class EdgeDelete(Component):
    def __init__(self):
        super().__init__()
    def update(self):
        super().update()
        transform = self.game_object.transform
        bool_x = self.detect(transform.position.x, game_dimensions.x / 2, -transform.scale.x * 10)
        bool_y = self.detect(transform.position.y, game_dimensions.y / 2, -transform.scale.y * 10)
        if bool_x or bool_y:
            self.game_object.destroy()

    def detect(self, a, b, extra_size = 0):
        if a >= (b - extra_size * 1.25):
            return True
        elif a <= (-b + extra_size):
            return True
        return False

class EdgeConstrict(Component):
    def __init__(self):
        super().__init__()

    def update(self):
        super().update()
        transform = self.game_object.transform
        transform.position.x = self.constrict(transform.position.x, game_dimensions.x / 2, transform.scale.x * 10)
        transform.position.y = self.constrict(transform.position.y, (game_dimensions.y + 10) / 2, transform.scale.y * 20)

    def constrict(self, a, b, extra_size = 0):
        if a >= (b - extra_size):
            a = b - extra_size
        elif a <= (-b + extra_size):
            a = -b + extra_size
        return a

def angle_to_vector(angle):
    radian = math.radians(angle)
    return Vector2(math.cos(radian), math.sin(radian))

class Bullet(Component):
    def __init__(self, angle = 90, rot_speed = 0, speed = 5):
        super().__init__()
        self.angle = angle
        self.speed = speed
        self.player_flag = False
        self.radius = 10
        self.rotation_speed = rot_speed
        self.extra_rotation = 0
        self.rot_delay = 0
        self.rot_delay_timer = 0
        self.extra_speed = 0
        self.acceleration = 0
        self.acceleration_delay = 0
        self.acceleration_delay_timer = 0

    def update(self):
        if game_manager.ended:
            self.game_object.destroy()
        extra_rot = self.extra_rotation
        if self.rot_delay > 0:
            self.rot_delay_timer += 1
        if self.acceleration_delay > 0:
            self.acceleration_delay_timer += 1
        new_angle = self.angle + extra_rot
        self.game_object.transform.position += (angle_to_vector(new_angle) * (self.speed + self.extra_speed))
        self.game_object.transform.rotation = (new_angle - 90)
        if (not self.rot_delay > 0) or self.rot_delay_timer >= self.rot_delay:
            self.extra_rotation += self.rotation_speed

        if (not self.acceleration_delay > 0) or self.acceleration_delay_timer >= self.acceleration_delay:
            self.extra_speed += self.acceleration


class Shooter(Component):
    def __init__(self, speed=15, timer=5, bands=3, spread=180, rot=0, reverse=0, radiance=0, color="red", radius=8, bullet_rot=0, bullet_rot_delay=0, bullet_acceleration=0, bullet_acceleration_delay=0, scale=Vector2(0.75, 1.5), player_flag = False):
        super().__init__()
        self.shoot_input = False
        self.max_shoot_timer = timer
        self.shoot_timer = self.max_shoot_timer
        self.bands = bands
        self.band_spread = spread
        self.bullet_speed = speed
        self.bullet_acceleration = bullet_acceleration
        self.bullet_acceleration_delay = bullet_acceleration_delay
        self.spawn_position = Vector2(0, 7)
        self.player_flag = player_flag
        self.color = color
        self.bullet_scale = scale
        self.radiance = radiance
        self.radiance_counter = 0
        self.max_radiance_counter = 5
        self.radiance_y_influence = False
        self.radius = radius
        self.sort_order = 1
        self.rot = rot
        self.current_rot_offset = 0
        self.max_reverse_time = reverse
        self.current_reverse_time = 0
        self.reversing = False
        self.bullet_rot = bullet_rot
        self.bullet_rot_delay = bullet_rot_delay

    def update(self):
        if game_manager.ended:
            return
        if self.shoot_timer > self.max_shoot_timer:
            self.shoot_timer = 0
            self.shoot()
        else:
            self.shoot_timer += 1

        if self.max_reverse_time > 0:
            if not self.reversing:
                self.current_reverse_time += 1
                self.current_rot_offset += self.rot
            else:
                self.current_rot_offset -= self.rot
                self.current_reverse_time -= 1

            if abs(self.current_reverse_time) > self.max_reverse_time - 1:
                if not self.reversing:
                    self.reversing = True
                else:
                    self.reversing = False

    def shoot(self):
        for i in range(0, self.bands):
            if len(bullets) >= bullet_limit:
                return
            bul = GameObject()
            bul.transform.position = self.game_object.transform.position + self.spawn_position
            sprite = bul.add_component(Sprite(self.color, "circle"))
            sprite.sort_order = self.sort_order
            bul.add_component(EdgeDelete())
            angle = self.game_object.transform.rotation + (self.band_spread / (self.bands + 1) * (i+1)) + (180-self.band_spread)/2 + self.current_rot_offset

            if self.radiance > 0:
                radianced = False
                if (abs(angle) - self.game_object.transform.rotation) > 10:
                    radianced = True
                    amount = self.radiance
                    if self.radiance_y_influence:
                        influence = ((game_dimensions.y / 8 - self.game_object.transform.position.y) - 15) / 1000
                        amount *= influence
                    if amount < 0:
                        amount = 0
                    angle += amount * (self.radiance_counter - (self.max_radiance_counter/2))
                if radianced:
                    self.radiance_counter += 1
                    if self.radiance_counter > self.max_radiance_counter:
                        self.radiance_counter = 0
            bul.transform.scale = self.bullet_scale
            bullet_script = bul.add_component(Bullet(angle = angle, speed = self.bullet_speed))
            bullet_script.rotation_speed = self.bullet_rot
            bullet_script.rot_delay = self.bullet_rot_delay
            bullet_script.player_flag = self.player_flag
            bullet_script.radius = self.radius
            bullet_script.acceleration = self.bullet_acceleration
            bullet_script.acceleration_delay = self.bullet_acceleration_delay
            bullets.append(bullet_script)

class Entity(Component):
    def __init__(self):
        super().__init__()
        self.move_input = Vector2()
        self.move_speed = 5
        self.dead = False
        self.active = True
        self.health = 1
        self.death_effect_color = "white"
        self.death_effect_scale = Vector2(2, 2)

    def take_damage(self, val):
        self.health -= val

    def collide(self, allow_player_bullets):
        if self.active == False:
            return
        for bullet in bullets:
            if bullet.player_flag == allow_player_bullets:
                transform = self.game_object.transform
                bullet_transform = bullet.game_object.transform
                if (transform.position - bullet_transform.position).magnitude() < bullet.radius:
                    self.take_damage(1)

                    if self.health <= 0:
                        self.die()
                        return

                    damage_particle = GameObject(position=bullet_transform.position).add_component(DamageParticle(self.death_effect_color))
                    reduced_angle = bullet.angle
                    if abs(reduced_angle) > 360:
                        reduced_angle -= 360 * 1 if reduced_angle > 0 else -1
                    if reduced_angle < 0:
                        damage_particle.going_up = False

    def start(self):
        super().start()

    def die(self):
        self.dead = True
        self.game_object.destroy()
        death_effect = GameObject(position=self.game_object.transform.position, scale=self.death_effect_scale, starting_comps=[DeathEffect(self.death_effect_color)])

    def update(self):
        if (self.active == False) or game_manager.ended:
            return
        self.game_object.transform.position.x += self.move_input.x * self.move_speed
        self.game_object.transform.position.y += self.move_input.y * self.move_speed

class BlackBars(Component):
    def __init__(self, dimensions):
        super().__init__()
        self.dimensions = dimensions

    def start(self):
        for i in range(0, 4):
            bar = GameObject()
            bar_sprite = bar.add_component(Sprite("black", "square"))
            bar_sprite.sort_order = 99
            bar_width = 40

            mult = 1
            if i % 2 == 0:
                mult = -1
            if i < 2:
                bar.transform.scale = Vector2(self.dimensions.x / 2, bar_width)
                bar.transform.position = Vector2(0, ((self.dimensions.y / 2) + bar_width * 10) * mult)
            else:
                bar.transform.scale = Vector2(bar_width, self.dimensions.y / 2)
                bar.transform.position = Vector2(((self.dimensions.x / 2) + bar_width * 10) * mult, 0)

class Lerp:
    def __init__(self, obj, attribute, target, speed, int_only = False):
        lerps.append(self)
        self.timer = 0
        self.lerping = True
        self.target = target
        self.obj = obj
        self.attribute = attribute
        self.speed = speed
        self.int_only = int_only

    def on_complete(self):
        pass

    def update(self):
        if self.lerping:
            self.timer += self.speed / 100
            current = getattr(self.obj, self.attribute)
            current += (self.target - current) * self.timer
            new_val = current
            if self.int_only:
                new_val = int(new_val)
            setattr(self.obj, self.attribute, new_val)
            if self.timer >= 0.3:
                self.timer = 0
                self.lerping = False
                self.on_complete()
                lerps.remove(self)

class GameManager(Component):
    def __init__(self):
        self.current_move_speed_index = 0
        self.score = 0
        self.score_text = None
        self.ended = False

    def start(self):
        self.score_text = GameObject().add_component(Text(color="white", font_size=13, align="left"))
        self.score_text.game_object.transform.position = Vector2(230, 300)
        self.score_text.sort_order = 1000
        self.set_score(0)

    def refresh_text(self):
        self.score_text.text = "Score: " + str(self.score)

    def add_score(self, val):
        self.score += val
        if self.score < 0:
            self.score = 0
        self.refresh_text()

    def set_score(self, val):
        self.score = val
        if self.score < 0:
            self.score = 0
        self.refresh_text()

    def update(self):
        for num in range(0, 10):
            if input_manager.get_key(str(num)):
                self.current_move_speed_index = num - 1

    def end_game(self):
        self.ended = True
        self.score_text.align = "center"
        Lerp(self.score_text, "font_size", 45, speed=1, int_only=True)
        self.score_text.game_object.transform.tween_position(Vector2(0, 0), speed=1)

class Player(Entity):
    def __init__(self):
        super().__init__()
        self.move_speeds = [8, 6, 4, 2]
        self.sprite = GameObject()
        self.health = 1
        self.invincibility = True
        self.death_effect_color = "red"
        self.living_score_timer = 0
        self.living_score_max_time = 25

        self.wide_shooter = None

    def start(self):
        super().start()
        sprite = self.sprite.add_component(Sprite())
        sprite.sort_order = -2
        self.sprite.transform.ignore_parent_scale = True
        self.sprite.transform.parent = self.game_object.transform
        self.sprite.transform.scale = Vector2(2, 1)
        screen.ontimer(self.end_invincibility, 1000)

        self.wide_shooter = self.game_object.add_component(
            Shooter(speed=30, timer=2, bands=5, spread=25, radius=16, player_flag=True, color="turquoise4"))
        self.wide_shooter.bullet_scale = Vector2(0.25, 2)
        self.wide_shooter.radiance = 5
        self.wide_shooter.radiance_y_influence = True
        self.wide_shooter.sort_order = -1

    def end_invincibility(self):
        self.invincibility = False

    def die(self):
        if self.invincibility:
            return

        super().die()
        game_manager.add_score(-100)
        screen.ontimer(spawn_player, 1000)

    def update(self):
        if game_manager.ended:
            return
        super().update()
        self.collide(allow_player_bullets=False)
        index = game_manager.current_move_speed_index
        if not self.dead:
            self.living_score_timer += 1
            if self.living_score_timer >= self.living_score_max_time:
                game_manager.add_score(1)
                self.living_score_timer = 0
        if index < len(self.move_speeds):
            self.move_speed = self.move_speeds[index]
        if input_manager.get_key("Up") or input_manager.get_key("w"):
            self.move_input.y = 1
        elif input_manager.get_key("Down") or input_manager.get_key("s"):
            self.move_input.y = -1
        else:
            self.move_input.y = 0

        if input_manager.get_key("Left") or input_manager.get_key("a"):
            self.move_input.x = -1
        elif input_manager.get_key("Right") or input_manager.get_key("d"):
            self.move_input.x = 1
        else:
            self.move_input.x = 0

class DeathEffect(Component):
    def __init__(self, color):
        super().__init__()
        self.color = color

    def start(self):
        sprites = []
        outer_circle = self.game_object.add_component(Sprite(self.color, "circle"))
        outer_circle.sort_order = 5
        sprites.append(outer_circle)

        lifetime = 200
        blinks = 4
        segment_duration = int(lifetime/blinks)
        for i in range(1, blinks + 1):
            for s in sprites:
                screen.ontimer(s.toggle_visibility, segment_duration * i)
        screen.ontimer(self.game_object.destroy, segment_duration * (blinks + 2))

class DamageParticle(Component):
    def __init__(self, color):
        super().__init__()
        self.color = color
        self.speed = random.randint(35, 55)
        self.t = 0
        self.graphic_objects = []
        self.going_up = True

    def start(self):
        for i in range(0, 3):
            graphic_object = GameObject()
            graphic_object.add_component(Sprite("white", "circle"))
            graphic_object.transform.parent = self.game_object.transform
            graphic_object.transform.local_position = Vector2(0, -10)
            graphic_object.transform.local_scale = Vector2(0.5, 1)
            self.graphic_objects.append(graphic_object)

    def update(self):
        if self.game_object.transform.scale.x > 0.01:
            self.t += 1
            self.game_object.transform.scale.x -= 0.1
            self.game_object.transform.scale.y += 0.1
            mult = 1
            if not self.going_up:
                mult = -1
            self.game_object.transform.position.y += (self.speed/10) * mult
        else:
            self.game_object.destroy()
        for i in range(0, len(self.graphic_objects)):
            graphic_object = self.graphic_objects[i]
            graphic_object.transform.local_position.x = (i-3/2) * self.t * 1

class Background(Component):
    def __init__(self):
        super().__init__()
        self.slides = []
        self.scroll_rate = 2

    def start(self):
        for i in range(0, 2):
            game_object = GameObject()
            game_object.transform.position = Vector2(0, i * 900)
            game_object.transform.parent = self.game_object.transform
            sprite = game_object.add_component(Sprite("white", "bg.gif"))
            sprite.sort_order = -99

    def update(self):
        if game_manager.ended:
            return
        self.game_object.transform.position.y -= self.scroll_rate
        if abs(self.game_object.transform.position.y) >= 900:
            self.game_object.transform.position.y = 0

class Enemy(Entity):
    def __init__(self, health=25, events=[]):
        super().__init__()
        self.health = health
        self.shooters = []
        self.events = events
        self.death_effect_scale = Vector2(3, 3)

    def add_shooter(self, shooter):
        self.game_object.add_component(shooter)
        self.shooters.append(shooter)

    def clear_shooters(self):
        for shooter in self.shooters:
            self.game_object.remove_component(shooter)
        self.shooters.clear()

    def die(self):
        super().die()
        game_manager.add_score(500)

    def event_routine(self):
        for event in self.events:
            if callable(event):
                event()
            else:
               for frame in event:
                   if self.dead:
                       return
                   yield

    def update(self):
        super().update()
        self.collide(allow_player_bullets=True)

    def take_damage(self, val):
        super().take_damage(val)
        game_manager.add_score(1)

class EnemySequencer(Component):
    def __init__(self):
        super().__init__()
        self.enemies = []

    def routine(self):
        for i in range(0, len(self.enemies)):
            enemy = self.enemies[i]
            enemy.active = True
            yield from enemy.event_routine()
        yield from wait_for_seconds(2)
        yield game_manager.end_game()

bullet_limit = 1000
bullets = []
render_objects = []
game_objects = []
lerps = []
coroutines = []

screen = turtle.Screen()

screen.tracer(0, 0)
screen.delay(0)

screen.title("Galaga")
screen_dimensions = Vector2(720, 700)
game_dimensions = Vector2(420, 700)
black_bars = GameObject().add_component(BlackBars(game_dimensions))
screen.setup(screen_dimensions.x, screen_dimensions.y)

screen.register_shape("bg.gif")

input_manager = Input()
background = GameObject().add_component(Background())
enemy_sequencer = GameObject().add_component(EnemySequencer())

def spawn_player():
    player_object = GameObject(position=Vector2(0, -200), starting_comps=[Sprite("blue", "circle")])
    player_script = player_object.add_component(Player())
    player_object.add_component(EdgeConstrict())

    player_object.transform.scale = Vector2(0.25, 0.25)
    return player_script

def create_enemy(health = 125, events = []):
    enemy_object = GameObject(position=Vector2(0, 400), starting_comps=[Sprite()])
    enemy_object.transform.rotation = -180
    enemy = enemy_object.add_component(Enemy(health=health, events=events))
    enemy.active = False
    return enemy
player = spawn_player()
game_manager = GameObject().add_component(GameManager())

enemy_1 = create_enemy(health=55, events=[
    lambda: enemy_1.game_object.transform.tween_position(Vector2(0, 325), speed=0.5),
    wait_for_seconds(2),
    lambda: enemy_1.add_shooter(Shooter(timer=4, rot=4, reverse=5, speed=8, bands=7, spread=180, color="turquoise")),
    wait_for_seconds(5),
    lambda: enemy_1.game_object.transform.tween_position(Vector2(-100, 325), speed=0.5),
    wait_for_seconds(5),
    lambda: enemy_1.game_object.transform.tween_position(Vector2(0, 325), speed=0.5),
    wait_for_seconds(5),
    lambda: enemy_1.game_object.transform.tween_position(Vector2(100, 325), speed=0.5),
    wait_for_seconds(5),
    lambda: enemy_1.game_object.transform.tween_position(Vector2(0, 325), speed=0.5),
    wait_for_seconds(5),
    lambda: enemy_1.clear_shooters(),
    wait_for_seconds(2),
    lambda: enemy_1.game_object.transform.tween_position(Vector2(0, 500), 0.5),
    wait_for_seconds(4),
    lambda: enemy_1.game_object.destroy()
])
enemy_sequencer.enemies.append(enemy_1)

enemy_2 = create_enemy(health=55, events=[
    lambda: enemy_2.game_object.transform.tween_position(Vector2(0, 325), speed=0.5),
    wait_for_seconds(4),
    lambda: enemy_2.add_shooter(Shooter(timer=4.5, rot=0.5, reverse=10, speed=8, bands=7, spread=160, color="turquoise")),
    lambda: enemy_2.add_shooter(Shooter(timer=6.5, rot=5, reverse=5, speed=8, bands=5, bullet_rot = 0.5, spread=160, color="aquamarine")),
    wait_for_seconds(5),
    lambda: enemy_2.game_object.transform.tween_position(Vector2(125, 325), speed=0.5),
    lambda: enemy_2.game_object.transform.tween_rotation(-180 - 25, speed=0.5),
    wait_for_seconds(5),
    lambda: enemy_2.game_object.transform.tween_position(Vector2(0, 325), speed=0.5),
    lambda: enemy_2.game_object.transform.tween_rotation(-180, speed=0.5),
    wait_for_seconds(5),
    lambda: enemy_2.game_object.transform.tween_position(Vector2(-125, 325), speed=0.5),
    lambda: enemy_2.game_object.transform.tween_rotation(-180 + 25, speed=0.5),
    wait_for_seconds(5),
    lambda: enemy_2.game_object.transform.tween_position(Vector2(0, 325), speed=0.5),
    lambda: enemy_2.game_object.transform.tween_rotation(-180, speed=0.5),
    wait_for_seconds(5),
    lambda: enemy_2.game_object.transform.tween_position(Vector2(125, 325), speed=0.5),
    lambda: enemy_2.game_object.transform.tween_rotation(-180 - 25, speed=0.5),
    wait_for_seconds(5),
    lambda: enemy_2.game_object.transform.tween_position(Vector2(0, 325), speed=0.5),
    lambda: enemy_2.game_object.transform.tween_rotation(-180, speed=0.5),
    wait_for_seconds(5),
    lambda: enemy_2.game_object.transform.tween_position(Vector2(0, 425), speed=0.5),
    wait_for_seconds(5),
    lambda: enemy_2.game_object.destroy()
])
enemy_sequencer.enemies.append(enemy_2)

enemy_3 = create_enemy(health=155, events=[
    lambda: enemy_3.game_object.transform.tween_position(Vector2(0, 325), speed=0.5),
    wait_for_seconds(4),
    lambda: enemy_3.add_shooter(Shooter(timer=7, rot=1, reverse=5, speed=7, bands=5, bullet_rot=-0.5, bullet_acceleration=0.1, bullet_acceleration_delay=20, color="turquoise", scale=Vector2(2,2), radius=18)),
    lambda: enemy_3.add_shooter(Shooter(timer=7, rot=1, reverse=5, speed=7, bands=5, bullet_rot=0.25, bullet_acceleration=0.1, bullet_acceleration_delay=20, color="aquamarine", scale=Vector2(2,2), radius=18)),
    lambda: enemy_3.add_shooter(Shooter(timer=18, rot=5, reverse=3, speed=9, bands=3, bullet_rot=1, bullet_rot_delay=10, color="turquoise3", scale=Vector2(4,4), radius=36)),
    wait_for_seconds(2),
    wait_for_seconds(50),
    lambda: enemy_3.clear_shooters(),
    wait_for_seconds(5),
    lambda: enemy_3.game_object.transform.tween_position(Vector2(0, 400), speed=0.1),
    wait_for_seconds(5),
    lambda: enemy_3.game_object.destroy()
])
enemy_sequencer.enemies.append(enemy_3)

start_coroutine(enemy_sequencer.routine())

def refresh_screen():
    ros = render_objects
    ros.sort(key=lambda r: r.sort_order)
    for r in ros:
        r.render()

def game_loop():
    for game_object in game_objects:
        game_object.update()
    for lerp in lerps:
        lerp.update()
    for coroutine in coroutines:
        try:
            next(coroutine)
        except StopIteration:
            coroutines.remove(coroutine)
    refresh_screen()
    input_manager.update()
    screen.ontimer(game_loop, 16)

game_loop()

refresh_screen()
screen.mainloop()
