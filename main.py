import math
import sys
import time
import turtle

sys.setrecursionlimit(100)

# Debug flag - set to True to show FPS and bullet count
debug = True

# Invincibility time in milliseconds
invincibility_time = 3000

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

    def sqr_magnitude(self):
        return self.x**2 + self.y**2

    def lerp(self, other, t):
        return self + (other - self) * t

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
                self.scale = self.parent.scale + self.local_scale
            self.rotation = self.parent.rotation + self.local_rotation

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, val: "Transform"):
        self._parent = val
        val.children.append(self)
        self.on_parent()

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
            scale = Vector2()
        if starting_comps is None:
            starting_comps = []

        self.transform = self.add_component(Transform())
        self.transform.position = position
        game_objects.append(self)

        for comp in starting_comps:
            self.add_component(comp)

    def destroy(self):
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
    def __init__(self, text = " ", color = "black", font_size = "54", font = "arial"):
        self.text = text
        self.color = color
        self.font = font
        self.font_size = font_size
        super().__init__()

    def pseudostamp(self):
        super().pseudostamp()
        self.pen.color(self.color)
        self.pen.write(self.text, font=(self.font, self.font_size), align="center")

class BulletRenderer(RenderObject):
    def __init__(self):
        super().__init__()
        self.sort_order = 2
        self.current_color = None
        self.current_shape = None
        self.current_scale = None
    
    def render(self):
        self.pen.clear()
        if not self.visible:
            return
            
        # Optimization: Removed sorting to save CPU cycles. 
        # Assuming bullets are naturally grouped by creation time/type.
        
        # Reset state trackers
        self.current_color = None
        self.current_shape = None
        self.current_scale = None
        self.current_heading = None
        
        # Cache pen methods for speed
        pen = self.pen
        pen_color = pen.color
        pen_shape = pen.shape
        pen_shapesize = pen.shapesize
        pen_setheading = pen.setheading
        pen_goto = pen.goto
        pen_stamp = pen.stamp
            
        for bullet in bullets:
            # Only change pen state if necessary
            if self.current_color != bullet.color:
                pen_color(bullet.color)
                self.current_color = bullet.color
            
            if self.current_shape != bullet.shape:
                pen_shape(bullet.shape)
                self.current_shape = bullet.shape
                
            if self.current_scale != (bullet.scale.x, bullet.scale.y):
                pen_shapesize(stretch_len=bullet.scale.x, stretch_wid=bullet.scale.y)
                self.current_scale = (bullet.scale.x, bullet.scale.y)

            # Optimization: Only change heading if necessary
            target_heading = bullet.angle - 90
            if self.current_heading != target_heading:
                pen_setheading(target_heading)
                self.current_heading = target_heading

            pen_goto(bullet.position.x, bullet.position.y)
            pen_stamp()

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
        bool_x = self.detect(transform.position.x, screen_dimensions.x / 2, -transform.scale.x * 10)
        bool_y = self.detect(transform.position.y, screen_dimensions.y / 2, -transform.scale.y * 10)
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
        transform.position.x = self.constrict(transform.position.x, screen_dimensions.x / 2, transform.scale.x * 10)
        transform.position.y = self.constrict(transform.position.y, (screen_dimensions.y + 10) / 2, transform.scale.y * 20)

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
    def __init__(self, angle = 90, speed = 5):
        super().__init__()
        self.angle = angle
        self.speed = speed
        self.player_flag = False
        self.radius = 10
        self.color = "white"
        self.shape = "circle"
        self.velocity = angle_to_vector(self.angle) * self.speed

    def start(self):
        self.transform = self.game_object.transform

    def update(self):
        self.transform.position += self.velocity
        self.transform.rotation = self.angle - 90

class SimpleBullet:
    def __init__(self, position, velocity, angle, color, shape, radius, player_flag, scale):
        self.position = position
        self.velocity = velocity
        self.angle = angle
        self.color = color
        self.shape = shape
        self.radius = radius
        self.player_flag = player_flag
        self.scale = scale
        self.active = True

class BulletManager(Component):
    def __init__(self):
        super().__init__()
        
    def update(self):
        global bullets
        # Update all bullets
        for bullet in bullets:
            # Optimization: Avoid Vector2 allocation by modifying x/y directly
            bullet.position.x += bullet.velocity.x
            bullet.position.y += bullet.velocity.y
            
            # Bounds check (EdgeDelete logic)
            # Tightened bounds to remove bullets as soon as they leave the visible screen
            # screen_dimensions.x / 2 = 210
            # screen_dimensions.y / 2 = 350
            # radius approx 10
            
            if (bullet.position.x >= 220 or bullet.position.x <= -220 or 
                bullet.position.y >= 360 or bullet.position.y <= -360):
                bullet.active = False
                
        # Remove inactive bullets
        # List comprehension is faster than manual loop
        bullets[:] = [b for b in bullets if b.active]

class Shooter(Component):
    def __init__(self, speed=15, timer=5, bands=3, spread=180, rot=0, backwards=0, radiance=0, color="red", radius=8, player_flag = False):
        super().__init__()
        self.shoot_input = False
        self.max_shoot_timer = timer
        self.shoot_timer = self.max_shoot_timer
        self.bands = bands
        self.band_spread = spread
        self.bullet_speed = speed
        self.spawn_position = Vector2(0, 7)
        self.player_flag = player_flag
        self.color = color
        self.bullet_scale = Vector2(1, 1)
        self.radiance = radiance
        self.radiance_counter = 0
        self.max_radiance_counter = 5
        self.radiance_y_influence = False
        self.radius = radius
        self.sort_order = 1
        self.rotation_speed = rot
        self.current_rot_offset = 0
        self.max_reverse_time = backwards
        self.current_reverse_time = 0
        self.reversing = False

    def update(self):
        if self.shoot_timer > self.max_shoot_timer:
            self.shoot_timer = 0
            self.shoot()
        else:
            self.shoot_timer += 1

        if self.max_reverse_time > 0:
            if not self.reversing:
                self.current_reverse_time += 1
                self.current_rot_offset += self.rotation_speed
            else:
                self.current_rot_offset -= self.rotation_speed
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
            
            # Calculate position
            pos = self.game_object.transform.position + self.spawn_position
            
            # Calculate angle
            angle = self.game_object.transform.rotation + (self.band_spread / (self.bands + 1) * (i+1)) + (180-self.band_spread)/2 + self.current_rot_offset

            if self.radiance > 0:
                radianced = False
                if (abs(angle) - self.game_object.transform.rotation) > 10:
                    radianced = True
                    amount = self.radiance
                    if self.radiance_y_influence:
                        influence = ((screen_dimensions.y / 8 - self.game_object.transform.position.y) - 15) / 1000
                        amount *= influence
                    if amount < 0:
                        amount = 0
                    angle += amount * (self.radiance_counter - (self.max_radiance_counter/2))
                if radianced:
                    self.radiance_counter += 1
                    if self.radiance_counter > self.max_radiance_counter:
                        self.radiance_counter = 0
            
            # Create SimpleBullet instead of GameObject
            velocity = angle_to_vector(angle) * self.bullet_speed
            
            # Create a copy of scale to avoid reference issues
            scale = Vector2(self.bullet_scale.x, self.bullet_scale.y)
            
            new_bullet = SimpleBullet(
                position=pos,
                velocity=velocity,
                angle=angle,
                color=self.color,
                shape="circle",
                radius=self.radius,
                player_flag=self.player_flag,
                scale=scale
            )
            bullets.append(new_bullet)

class Entity(Component):
    def __init__(self):
        super().__init__()
        self.move_input = Vector2()
        self.move_speed = 5
        self.dead = False
        self.health = 1

    def collide(self, allow_player_bullets):
        for bullet in bullets:
            if bullet.player_flag == allow_player_bullets:
                transform = self.game_object.transform
                # SimpleBullet has position directly
                if (transform.position - bullet.position).sqr_magnitude() < bullet.radius**2:
                    self.health -= 1
                    if self.health <= 0:
                        self.die()
                        return

    def start(self):
        super().start()

    def die(self):
        self.game_object.destroy()

    def update(self):
        if self.dead:
            self.die()
            return

        self.game_object.transform.position.x += self.move_input.x * self.move_speed
        self.game_object.transform.position.y += self.move_input.y * self.move_speed

class PathPoint:
    def __init__(self, position, rotation=-90, wait_time=1):
        self.position = position
        self.rotation = rotation
        self.wait_time = wait_time

class BlackBars(Component):
    def __init__(self):
        super().__init__()

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
                bar.transform.scale = Vector2(screen_dimensions.x / 2, bar_width)
                bar.transform.position = Vector2(0, ((screen_dimensions.y / 2) + bar_width * 10) * mult)
            else:
                bar.transform.scale = Vector2(bar_width, screen_dimensions.y / 2)
                bar.transform.position = Vector2(((screen_dimensions.x / 2) + bar_width * 10) * mult, 0)

class Enemy(Entity):
    def __init__(self, health=25, path_points=None):
        super().__init__()
        self.path_points = path_points
        self.path_lerp_timer = 0
        self.health = health

    def start(self):
        pass

    def go_to_path_point(self, path_point):
        self.game_object.transform.position = self.game_object.transform.position.lerp(path_point.position, self.path_lerp_timer)
        yield

    def update(self):
        super().update()
        self.collide(allow_player_bullets=True)

class GameManager:
    def __init__(self):
        self.death_count = 0
        self.current_move_speed_index = 0

    def update(self):
        for num in range(0, 10):
            if input_manager.get_key(str(num)):
                self.current_move_speed_index = num - 1

class Player(Entity):
    def __init__(self):
        super().__init__()
        self.move_speeds = [8, 6, 4, 2]
        self.sprite = GameObject()
        self.health = 1
        self.invincibility = True

    def start(self):
        super().start()
        sprite = self.sprite.add_component(Sprite())
        sprite.sort_order = -2
        self.sprite.transform.ignore_parent_scale = True
        self.sprite.transform.parent = self.game_object.transform
        self.sprite.transform.scale = Vector2(2, 1)
        screen.ontimer(self.end_invincibility, invincibility_time)

    def end_invincibility(self):
        self.invincibility = False

    def die(self):
        if self.invincibility:
            return
        super().die()
        screen.ontimer(spawn_player, 1000)

    def update(self):
        super().update()
        self.collide(allow_player_bullets=False)
        self.move_speed = self.move_speeds[game_manager.current_move_speed_index]
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

class PlayerDeathEffect(Component):
    def __init__(self):
        super().__init__()
        self.effect_object = GameObject()
        self.sprite = self.effect_object.add_component(Sprite("white", "circle"))
        self.effect_object.transform.scale = Vector2(10, 10)

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
        self.game_object.transform.position.y -= self.scroll_rate
        if abs(self.game_object.transform.position.y) >= 900:
            self.game_object.transform.position.y = 0
bullet_limit = 1000
bullets = []
bullet_pool = []
render_objects = []
game_objects = []

# Debug variables for FPS tracking
frame_counter = 0
last_frame_time = time.time()
frame_times = []
perf_metrics = {
    'update': 0,
    'render_prep': 0,
    'screen_update': 0
}


screen = turtle.Screen()

screen.tracer(0, 0)
screen.delay(0)
screen.title("Galaga")
screen_dimensions = Vector2(420, 700)
screen.setup(screen_dimensions.x, screen_dimensions.y)

screen.register_shape("bg.gif")

input_manager = Input()
game_manager = GameManager()
black_bars = GameObject().add_component(BlackBars())
background = GameObject().add_component(Background())
bullet_renderer = GameObject().add_component(BulletRenderer())
bullet_manager = GameObject().add_component(BulletManager())

# Create debug FPS text (only visible if debug = True)
fps_text_object = GameObject(position=Vector2(50, 320))
fps_text = fps_text_object.add_component(Text("FPS: 0 | Bul: 0", "yellow", "14", "courier"))
fps_text.sort_order = 100
fps_text.visible = debug

# Create debug Performance text
perf_text_object = GameObject(position=Vector2(50, 280))
perf_text = perf_text_object.add_component(Text("", "yellow", "10", "courier"))
perf_text.sort_order = 100
perf_text.visible = debug

# Create background for FPS text
if debug:
    fps_bg_object = GameObject(position=Vector2(50, 325))
    fps_bg = fps_bg_object.add_component(Sprite("black", "square"))
    fps_bg.game_object.transform.scale = Vector2(10, 1.5)
    fps_bg.sort_order = 99

def spawn_player():
    player_object = GameObject(position=Vector2(0, -200), starting_comps=[Sprite("blue", "circle")])
    player_script = player_object.add_component(Player())
    player_object.add_component(EdgeConstrict())
    wide_shooter = player_object.add_component(Shooter(speed=30, timer=2, color="turquoise4", bands=5, spread=25, radius=16, player_flag=True))
    wide_shooter.bullet_scale = Vector2(0.25, 2)
    wide_shooter.radiance = 5
    wide_shooter.radiance_y_influence = True
    wide_shooter.sort_order = -1

    player_object.transform.scale = Vector2(0.5, 0.5)

spawn_player()

enemy = GameObject(starting_comps=[Sprite(), Enemy(health=125)])
shot1 = enemy.add_component(Shooter(timer=2, rot=4, backwards=5, speed=12, bands=11, spread=140, color="turquoise"))
shot1.bullet_scale = Vector2(0.75, 1.5)
shot2 = enemy.add_component(Shooter(timer=7, rot=-2, backwards=5, speed=12, bands=11, spread=140, color="aquamarine"))
shot2.bullet_scale = Vector2(0.75, 1.5)
enemy.transform.position = Vector2(0, 325)
enemy.transform.rotation = -180

def refresh_screen():
    t_start = time.time()
    ros = render_objects
    ros.sort(key=lambda r: r.sort_order)
    for r in ros:
        r.render()
    t_render = time.time()
    screen.update()
    t_end = time.time()
    
    if debug:
        perf_metrics['render_prep'] = (t_render - t_start) * 1000
        perf_metrics['screen_update'] = (t_end - t_render) * 1000

def game_loop():
    global frame_counter, last_frame_time
    
    t_start = time.time()
    for game_object in game_objects:
        game_object.update()
    t_update = time.time()
    
    if debug:
        perf_metrics['update'] = (t_update - t_start) * 1000

    refresh_screen()
    input_manager.update()
    game_manager.update()
    
    # Update FPS counter every 60 frames if debug is enabled
    if debug:
        frame_counter += 1
        if frame_counter >= 60:
            frame_counter = 0
            current_time = time.time()
            frame_time = current_time - last_frame_time
            last_frame_time = current_time
            
            frame_times.append(frame_time / 60)  # Average per frame
            if len(frame_times) > 10:
                frame_times.pop(0)
            
            avg_frame_time = sum(frame_times) / len(frame_times)
            fps = 1 / avg_frame_time if avg_frame_time > 0 else 0
            fps_text.text = f"FPS: {int(fps)} | Bul: {len(bullets)}"
            perf_text.text = f"Upd: {perf_metrics['update']:.1f}ms | Prep: {perf_metrics['render_prep']:.1f}ms | Draw: {perf_metrics['screen_update']:.1f}ms"
            print(f"FPS: {int(fps)} | Upd: {perf_metrics['update']:.1f}ms | Prep: {perf_metrics['render_prep']:.1f}ms | Draw: {perf_metrics['screen_update']:.1f}ms | Bul: {len(bullets)}")
            
    # Optimization: Reduced delay to 0 to run as fast as possible
    screen.ontimer(game_loop, 0)

game_loop()

refresh_screen()
screen.mainloop()
