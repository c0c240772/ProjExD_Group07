import os
import random
import sys
import time
import pygame as pg

WIDTH = 720
HEIGHT = 570
CELL_SIZE = 30

os.chdir(os.path.dirname(os.path.abspath(__file__)))


class Pacman(pg.sprite.Sprite):
    delta = {
        pg.K_UP: (0, -1),
        pg.K_DOWN: (0, 1),
        pg.K_LEFT: (-1, 0),
        pg.K_RIGHT: (1, 0),
    }

    def __init__(self, maze, xy):
        super().__init__()
        self.maze = maze
        img = pg.transform.rotozoom(pg.image.load("fig/2.png"), 0, 0.9)
        self.image = pg.transform.flip(img, True, False)
        self.rect = self.image.get_rect()
        self.grid_x, self.grid_y = xy
        self.update_rect()

    def update_rect(self):
        self.rect.center = (
            self.grid_x * CELL_SIZE + CELL_SIZE // 2,
            self.grid_y * CELL_SIZE + CELL_SIZE // 2
        )

    def move(self, key):
        if key not in self.delta:
            return

        dx, dy = self.delta[key]
        nx = self.grid_x + dx
        ny = self.grid_y + dy

        if 0 <= ny < len(self.maze) and 0 <= nx < len(self.maze[0]):
            if self.maze[ny][nx] not in (1, 3):
                self.grid_x, self.grid_y = nx, ny
                self.update_rect()
                if self.maze[ny][nx] == 0:
                    self.maze[ny][nx] = 2


class Enemy(pg.sprite.Sprite):
    def __init__(self, maze, xy, img_name):
        super().__init__()
        self.maze = maze
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/{img_name}"), 0, 0.1)
        self.rect = self.image.get_rect()
        self.grid_x, self.grid_y = xy
        self.update_rect()
        self.move_timer = 0
        self.move_interval = 15
        self.stop_until = 0

    def update_rect(self):
        self.rect.center = (
            self.grid_x * CELL_SIZE + CELL_SIZE // 2,
            self.grid_y * CELL_SIZE + CELL_SIZE // 2
        )

    def update(self):
        if time.time() < self.stop_until:
            return

        self.move_timer += 1
        if self.move_timer < self.move_interval:
            return

        self.move_timer = 0
        moves = [(0, -1), (0, 1), (-1, 0), (1, 0)]
        random.shuffle(moves)

        for dx, dy in moves:
            nx = self.grid_x + dx
            ny = self.grid_y + dy
            if 0 <= ny < len(self.maze) and 0 <= nx < len(self.maze[0]):
                if self.maze[ny][nx] not in (1, 3):
                    self.grid_x, self.grid_y = nx, ny
                    self.update_rect()
                    break


class Score:
    def __init__(self):
        self.font = pg.font.Font(None, 40)
        self.value = 0

    def add(self, p):
        self.value += p

    def draw(self, screen):
        img = self.font.render(f"Score: {self.value}", True, (255, 255, 255))
        screen.blit(img, (10, 10))


class Maze:
    def __init__(self):
        self.data = [
            [3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3],
            [3,2,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,3],
            [3,1,1,1,1,0,1,0,1,1,1,1,1,1,1,1,1,1,1,1,1,0,1,3],
            [3,0,1,1,1,0,1,0,0,0,0,0,0,0,0,0,0,1,1,1,0,0,1,3],
            [3,0,1,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,1,3],
            [3,0,1,0,0,1,1,1,1,1,0,1,0,1,1,1,1,1,0,1,0,1,1,3],
            [3,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,4,0,1,3],
            [3,1,1,1,1,0,1,0,1,1,1,0,1,1,1,0,0,1,1,1,1,1,1,3],
            [3,1,1,1,1,0,1,0,1,0,0,0,0,0,1,0,0,1,1,1,1,1,1,3],
            [3,0,4,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,3],
            [3,1,1,1,1,0,1,0,1,0,0,0,0,0,1,0,0,1,1,1,1,1,1,3],
            [3,1,1,1,1,0,1,0,1,1,1,1,1,1,1,0,0,1,1,1,1,1,1,3],
            [3,0,0,0,0,0,1,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,1,3],
            [3,1,1,0,0,1,1,1,1,1,0,1,0,1,1,1,1,1,0,1,1,1,1,3],
            [3,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,4,0,1,3],
            [3,1,1,0,0,1,1,0,1,1,1,1,1,1,1,0,1,1,0,1,1,0,1,3],
            [3,1,1,0,0,0,1,0,0,0,0,0,0,0,0,0,1,1,0,1,1,0,1,3],
            [3,0,0,0,0,0,4,0,0,0,0,1,0,1,1,0,1,1,0,0,0,0,1,3],
            [3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3],
            [3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3]
        ]
        self.wall_color = (0, 0, 255)
        self.cookie_color = (255, 255, 0)
        self.time_item_img = pg.transform.rotozoom(
            pg.image.load("fig/時を止めるアイテム.png"), 0, 0.1
        )

    def draw(self, screen):
        for y in range(len(self.data)):
            for x in range(len(self.data[y])):
                v = self.data[y][x]
                if v in (1, 3):
                    pg.draw.rect(
                        screen, self.wall_color,
                        (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                    )
                elif v == 0:
                    pg.draw.circle(
                        screen, self.cookie_color,
                        (x * CELL_SIZE + CELL_SIZE // 2,
                         y * CELL_SIZE + CELL_SIZE // 2),
                        3
                    )
                elif v == 4:
                    rect = self.time_item_img.get_rect()
                    rect.center = (
                        x * CELL_SIZE + CELL_SIZE // 2,
                        y * CELL_SIZE + CELL_SIZE // 2
                    )
                    screen.blit(self.time_item_img, rect)

    def count_cookies(self):
        return sum(row.count(0) for row in self.data)


def Stop_time(enemies, sec):
    until = time.time() + sec
    for e in enemies:
        e.stop_until = until


def main():
    pg.init()
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    pg.display.set_caption("こうかまん")
    clock = pg.time.Clock()

    maze = Maze()
    score = Score()
    koukaman = Pacman(maze.data, (1, 1))

    enemies = pg.sprite.Group(
        Enemy(maze.data, (10, 2), "かまトゥ.png"),
        Enemy(maze.data, (12, 2), "ぱっちぃ.png")
    )

    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()

            if event.type == pg.KEYDOWN:
                koukaman.move(event.key)

        screen.fill((0, 0, 0))
        maze.draw(screen)

        # スコア加算
        if maze.data[koukaman.grid_y][koukaman.grid_x] == 2:
            score.add(10)

        # 時を止めるアイテム
        if maze.data[koukaman.grid_y][koukaman.grid_x] == 4:
            Stop_time(enemies, 3)
            maze.data[koukaman.grid_y][koukaman.grid_x] = 2

        # 敵との衝突
        for e in enemies:
            if e.grid_x == koukaman.grid_x and e.grid_y == koukaman.grid_y:
                font = pg.font.Font(None, 80)
                txt = font.render("GAME OVER", True, (255, 0, 0))
                screen.blit(txt, txt.get_rect(center=(WIDTH//2, HEIGHT//2)))
                pg.display.update()
                time.sleep(3)
                pg.quit()
                sys.exit()

        enemies.update()
        enemies.draw(screen)
        screen.blit(koukaman.image, koukaman.rect)
        score.draw(screen)

        pg.display.update()
        clock.tick(60)


if __name__ == "__main__":
    main()
