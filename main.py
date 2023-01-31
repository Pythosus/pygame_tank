import pygame
import sys
import os
import pygame_gui
from random import randint, choice


# загрузка картинки
def load_image(name, colorkey=None):
    fullname = os.path.join('data', name)
    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys.exit()
    image = pygame.image.load(fullname)
    if colorkey is not None:
        image = image.convert()
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    else:
        image = image.convert_alpha()
    return image


# функция чтения уровня из txt файла
def load_level(filename):
    filename = "data/" + filename
    with open(filename, 'r') as mapFile:
        level_map = [line.strip() for line in mapFile]
    max_width = max(map(len, level_map))
    return list(map(lambda x: x.ljust(max_width, '.'), level_map))


# функция генерации уровня
def generate_level(level):
    for y in range(len(level)):
        for x in range(len(level[y])):
            if level[y][x] == '#':
                Tile('wall', x, y)
            if level[y][x] == '.':
                Tile('sand', x, y)


# объевление базовых переменных
pygame.init()
size = width, height = 1280, 960
tile_width = tile_height = tile = 64
screen = pygame.display.set_mode(size)
clock = pygame.time.Clock()
fontUi = pygame.font.Font(None, 32)
all_sprites = pygame.sprite.Group()
pygame.display.set_caption('Two players Battle Tanks')
menu = True
game = True
running = True
upgrade_flag = False
name_map = 'map1.txt'
objects = []
bullets = []
upgrades = []
empty = []
used_coords = []
end_game = []
FPS = 60

# переменные кнопок(главное меню)
manager = pygame_gui.UIManager((1280, 960))
start_game = pygame_gui.elements.UIButton(
    relative_rect=pygame.Rect((512, 288), (256, 128)),
    text='Начать игру',
    manager=manager
)
exit = pygame_gui.elements.UIButton(
    relative_rect=pygame.Rect((512, 736), (256, 128)),
    text='Выйти',
    manager=manager
)
levels = pygame_gui.elements.ui_drop_down_menu.UIDropDownMenu(
    options_list=['Карта №1', 'Карта №2', 'Карта №3'],
    starting_option='Карта №1',
    relative_rect=pygame.Rect((512, 480), (256, 128)),
    manager=manager
)

# списки с данными о спрайтах для объектов
img_brick = load_image('wall.png')
img_empty = load_image('sand.png')
img_tanks = [load_image('red_main.png'),
             load_image('blue_main.png'),
             load_image('red_big_gun.png'),
             load_image('blue_big_gun.png')]
img_bangs = [load_image('boom1.png', -1), load_image('boom2.png', -1),
             load_image('boom3.png', -1), load_image('boom4.png', -1),
             load_image('boom5.png', -1), load_image('boom6.png', -1),
             load_image('boom7.png', -1), load_image('boom8.png', -1),
             load_image('boom9.png', -1), load_image('boom10.png', -1),
             load_image('boom11.png', -1)]

# словари с данными для объектов
tank_size = {'tank': (56, 24),
             'big_gun': ()}

bullet_dict = {'tank': [1, 'yellow'],
               'big_gun': [2, 'purple']}

tile_images = {
    'wall': load_image('wall.png'),
    'sand': load_image('sand.png')
}


# функция выхода
def terminate():
    pygame.quit()
    sys.exit()


# класс танков
class Tank:
    def __init__(self, color, px, py, drct, keys):
        objects.append(self)
        end_game.append(self)

        self.speed = 2
        self.rank = 0

        self.type = 'tank'
        self.color = color
        self.rect = pygame.Rect(px, py, tank_size['tank'][0], tank_size['tank'][1])
        self.direct = drct
        self.buttons = keys

        self.image = pygame.transform.rotate(img_tanks[self.rank], -90 * self.direct)
        self.mask = pygame.mask.from_surface(self.image)

        self.healpoints = 5

        self.bullet_damage = 1
        self.bullet_speed = 5
        self.shot_timer = 0
        self.shot_delay = 60

        self.degrade_timer = 0

        if color == 'blue':
            self.rank = 1

    def upgrade(self):
        self.type = 'big_gun'
        self.rank += 2
        self.bullet_damage += 2
        self.bullet_speed *= 3
        self.speed //= 2
        self.shot_delay *= 2
        self.degrade_timer += 600

    def degrade(self):
        self.type = 'tank'
        self.rank -= 2
        self.bullet_damage -= 2
        self.bullet_speed //= 2
        self.shot_delay //= 2
        self.speed *= 2

    def damage(self, dmg):
        self.healpoints -= dmg
        if self.healpoints <= 0:
            x = self.rect.x + 16
            y = self.rect.y + 16
            objects.remove(self)
            end_game.remove(self)
            Bang(x, y)

    def update(self):
        self.image = pygame.transform.rotate(img_tanks[self.rank], -90 * self.direct)
        self.rect = self.image.get_rect(center=self.rect.center)

        x = self.rect.x
        y = self.rect.y

        if keys[self.buttons[0]]:
            self.rect.x -= self.speed
            self.direct = 2
        elif keys[self.buttons[1]]:
            self.rect.y -= self.speed
            self.direct = 3
        elif keys[self.buttons[2]]:
            self.rect.x += self.speed
            self.direct = 0
        elif keys[self.buttons[3]]:
            self.rect.y += self.speed
            self.direct = 1

        for obj in objects:
            if obj != self and pygame.sprite.collide_mask(self, obj):
                self.rect.x = x
                self.rect.y = y

        if self.rect.x < 0 or self.rect.x > width - 60 or self.rect.y < 0 or self.rect.y > height - 60:
            self.rect.x = x
            self.rect.y = y

        if keys[self.buttons[4]] and self.shot_timer == 0:
            dir = [[1, 0], [0, 1], [-1, 0], [0, -1]]
            dx = dir[self.direct][0] * self.bullet_speed
            dy = dir[self.direct][1] * self.bullet_speed
            Bullet(self, self.rect.centerx, self.rect.centery, dx, dy, self.bullet_damage)
            self.shot_timer = self.shot_delay

        if self.shot_timer > 0:
            self.shot_timer -= 1

        if self.degrade_timer > 0:
            self.degrade_timer -= 1

        if self.type == 'big_gun' and self.degrade_timer == 0:
            self.degrade()

    def draw(self):
        screen.blit(self.image, self.rect)


# класс текстур(стена и песок)
class Tile:
    def __init__(self, tile_type, pos_x, pos_y):
        if tile_type == 'wall':
            objects.append(self)
            self.type = tile_type
            used_coords.append([pos_x, pos_y])
        else:
            empty.append(self)
            self.type = tile_type
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.image = tile_images[tile_type]
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect().move(
            tile_width * pos_x, tile_height * pos_y)

    def update(self):
        pass

    def draw(self):
        screen.blit(self.image, self.rect)


# класс снарядов
class Bullet:
    def __init__(self, parent, px, py, dx, dy, damage):
        bullets.append(self)
        self.parent = parent
        self.px = px
        self.py = py
        self.dx = dx
        self.dy = dy
        self.damage = damage

        self.size = bullet_dict[parent.type][0]
        self.color = bullet_dict[parent.type][1]

    def update(self):
        self.px += self.dx
        self.py += self.dy

        if self.px < 0 or self.px > width or self.py < 0 or self.py > height:
            bullets.remove(self)
        else:
            for obj in objects:
                if obj != self.parent:
                    if obj.rect.collidepoint(self.px, self.py):
                        bullets.remove(self)
                        if obj.type in ('tank', 'big_gun'):
                            obj.damage(self.damage)
                            break
                        else:
                            px = obj.pos_x
                            py = obj.pos_y
                            objects.remove(obj)
                            Bang(self.px, self.py)
                            Tile('sand', px, py)
                            break

    def draw(self):
        pygame.draw.circle(screen, self.color, (self.px, self.py), self.size)


# класс интерфейса (показатели здоровья у игроков)
class Interface:
    def __init__(self):
        pass

    def update(self):
        pass

    def draw(self):
        counter = 0
        for obj in objects:
            if obj.type in ('tank', 'big_gun'):
                pygame.draw.rect(screen, obj.color, (576 + 64 * counter, 8, 24, 24))

                text = fontUi.render(str(obj.healpoints), True, obj.color)
                rect = text.get_rect(center=(576 + 64 * counter + 32, 8 + 16))
                screen.blit(text, rect)
                counter += 1


# класс взрыва
class Bang:
    def __init__(self, x, y):
        self.type = 'bang'
        self.frame = 0
        self.px = x
        self.py = y
        self.image = img_bangs[int(self.frame)]
        self.rect = self.image.get_rect()
        objects.append(self)

    def update(self):
        self.frame += 0.25
        if self.frame >= 11:
            objects.remove(self)

    def draw(self):
        boom = img_bangs[int(self.frame)]
        rect = boom.get_rect(center=(self.px, self.py))
        screen.blit(boom, rect)


# класс частиц(звёздочек) которые вылетают при объявлении победителя
class Particle(pygame.sprite.Sprite):
    fire = [load_image("star.png")]
    for scale in (5, 10, 20):
        fire.append(pygame.transform.scale(fire[0], (scale, scale)))

    def __init__(self, pos, dx, dy):
        super().__init__(all_sprites)
        self.image = choice(self.fire)
        self.rect = self.image.get_rect()
        self.velocity = [dx, dy]
        self.rect.x, self.rect.y = pos
        self.gravity = 0.1

    def update(self):
        self.velocity[1] += self.gravity
        self.rect.x += self.velocity[0]
        self.rect.y += self.velocity[1]
        if not self.rect.colliderect(0, 0, 1280, 960):
            self.kill()


# создание частиц
def create_particles(position):
    particle_count = 20
    numbers = range(-5, 6)
    for _ in range(particle_count):
        Particle(position, choice(numbers), choice(numbers))


# класс улучшения для танков
class Upgrade:
    def __init__(self):
        x = randint(1, 19)
        y = randint(1, 14)
        while [x, y] in used_coords:
            x = randint(1, 19)
            y = randint(1, 14)
        print(x * tile, y * tile, 'upgrade')
        self.rect = pygame.Rect(x * tile, y * tile, tile, tile)
        self.image = load_image('upgrade.png')
        self.mask = pygame.mask.from_surface(self.image)
        upgrades.append(self)

    def update(self):
        for obj in objects:
            if obj.type in ('tank', 'big_gun') and pygame.sprite.collide_mask(self, obj):
                obj.upgrade()
                upgrades.remove(self)

    def draw(self):
        screen.blit(self.image, self.rect)


# вывод победителя на экран
def end_text(player):
    font = pygame.font.Font(None, 128)
    text = font.render(f'{player.title()} wins!', True, player)
    screen.blit(text, (480, 420))


# основной цикл
try:
    menu = True
    while running:
        while menu:
            screen.fill('#8B008B')
            time_delta = clock.tick(60) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    menu = False
                    game = False
                    running = False
                    end_game = False
                if event.type == pygame.USEREVENT:
                    if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                        if event.ui_element == start_game:
                            menu = False
                            game = True
                        if event.ui_element == exit:
                            menu = False
                            game = False
                            running = False
                            end_game = False
                    if event.user_type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
                        name_map = f'map{event.text[-1]}.txt'
                manager.process_events(event)
            manager.update(time_delta)
            manager.draw_ui(screen)
            pygame.display.update()

        objects = []
        bullets = []
        upgrades = []
        empty = []
        used_coords = []
        end_game = []
        Tank('red', 128, 480, 0, (pygame.K_a, pygame.K_w, pygame.K_d, pygame.K_s, pygame.K_SPACE))
        Tank('blue', 1152, 480, 2, (pygame.K_LEFT, pygame.K_UP, pygame.K_RIGHT, pygame.K_DOWN, pygame.K_KP_ENTER))
        upgrade_clock = 1
        upgrade_flag = False
        ui = Interface()
        generate_level(load_level(name_map))
        winner = ''
        while game:
            screen.fill('black')
            if upgrade_clock % 1200 == 0 and upgrade_clock > 0 and not upgrade_flag and len(upgrades) == 0:
                print(upgrade_clock)
                Upgrade()
                upgrade_flag = True
            if upgrade_flag:
                upgrade_clock = -600
                upgrade_flag = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    menu = False
                    game = False
                    running = False
                    end_game = False
            if len(end_game) == 1:
                winner = end_game[0].color
                game = False
                end_game = True
            keys = pygame.key.get_pressed()
            for e in empty:
                e.update()
            for bullet in bullets:
                bullet.update()
            for upg in upgrades:
                upg.update()
            for obj in objects:
                obj.update()
            ui.update()
            for e in empty:
                e.draw()
            for upg in upgrades:
                upg.draw()
            for bullet in bullets:
                bullet.draw()
            for obj in objects:
                obj.draw()
            ui.draw()
            pygame.display.flip()
            clock.tick(FPS)
            upgrade_clock += 1

        star = True
        while end_game:
            screen.fill('#8B008B')
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    menu = False
                    game = False
                    running = False
                    end_game = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    end_game = False
                    menu = True
            if star:
                for _ in range(15):
                    x = choice(range(128, 1152, 16))
                    y = choice(range(128, 832, 16))
                    create_particles(tuple([x, y]))
                star = False
            end_text(winner)
            all_sprites.update()
            all_sprites.draw(screen)
            pygame.display.flip()
            clock.tick(FPS)
    terminate()
except Exception as er:
    print(er)
