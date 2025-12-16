import math
import os
import random
import sys
import time
import pygame as pg


WIDTH = 720  # ゲームウィンドウの幅
HEIGHT = 570  # ゲームウィンドウの高さ
CELL_SIZE = 30  # セルサイズ
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内or画面外を判定し，真理値タプルを返す関数
    引数：こうかまんや敵などのRect
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate


class Pacman(pg.sprite.Sprite):
    """
    ゲームキャラクターに関するクラス
    """
    delta = {  # 押下キーと移動量の辞書
        pg.K_UP: (0, -1),
        pg.K_DOWN: (0, +1),
        pg.K_LEFT: (-1, 0),
        pg.K_RIGHT: (+1, 0),
    }

    def __init__(self, maze: list, xy: tuple[int, int]):
        """
        こうかとん画像Surfaceを生成する
        引数1 maze：迷路データ
        引数2 xy：こうかとん画像の位置座標タプル（グリッド座標）
        """
        super().__init__()
        self.maze = maze
        img = pg.transform.rotozoom(pg.image.load(f"fig/2.png"), 0, 0.9)
        self.image = pg.transform.flip(img, True, False)
        self.rect = self.image.get_rect()
        self.grid_x, self.grid_y = xy
        self.rect.center = (self.grid_x * CELL_SIZE + CELL_SIZE//2, 
                           self.grid_y * CELL_SIZE + CELL_SIZE//2)
        self.speed = 5

    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じてこうかまんを移動させる
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        """
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                new_grid_x = self.grid_x + mv[0]
                new_grid_y = self.grid_y + mv[1]
                
                # 迷路の範囲内かチェック
                if 0 <= new_grid_y < len(self.maze) and 0 <= new_grid_x < len(self.maze[0]):
                    # 壁でなければ移動（1:壁、3:外枠）
                    if self.maze[new_grid_y][new_grid_x] != 1 and self.maze[new_grid_y][new_grid_x] != 3:
                        self.grid_x = new_grid_x
                        self.grid_y = new_grid_y
                        self.rect.center = (self.grid_x * CELL_SIZE + CELL_SIZE//2,
                                          self.grid_y * CELL_SIZE + CELL_SIZE//2)
                        # クッキーを食べる
                        if self.maze[self.grid_y][self.grid_x] == 0:
                            self.maze[self.grid_y][self.grid_x] = 2
                        time.sleep(0.1)  # こうかとんの移動速度を遅くする
                break
        
        screen.blit(self.image, self.rect)


class Enemy(pg.sprite.Sprite):
    """
    敵に関するクラス
    """
    def __init__(self, maze: list, xy: tuple[int, int], img_name: str):
        """
        敵画像Surfaceを生成する
        引数1 maze：迷路データ
        引数2 xy：敵の初期位置（グリッド座標）
        引数3 img_name：敵の画像ファイル名
        """
        super().__init__()
        self.maze = maze
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/{img_name}"), 0, 0.1)
        self.rect = self.image.get_rect()
        self.grid_x, self.grid_y = xy
        self.rect.center = (self.grid_x * CELL_SIZE + CELL_SIZE//2,
                           self.grid_y * CELL_SIZE + CELL_SIZE//2)
        self.move_timer = 0
        self.move_interval = 10

    def update(self):
        """
        敵をランダムに移動させる
        """
        self.move_timer += 1
        if self.move_timer >= self.move_interval:
            self.move_timer = 0
            moves = [(0, -1), (0, 1), (-1, 0), (1, 0)]
            random.shuffle(moves)
            
            for mv in moves:
                new_grid_x = self.grid_x + mv[0]
                new_grid_y = self.grid_y + mv[1]
                
                if 0 <= new_grid_y < len(self.maze) and 0 <= new_grid_x < len(self.maze[0]):
                    if self.maze[new_grid_y][new_grid_x] != 1 and self.maze[new_grid_y][new_grid_x] != 3:
                        self.grid_x = new_grid_x
                        self.grid_y = new_grid_y
                        self.rect.center = (self.grid_x * CELL_SIZE + CELL_SIZE//2,
                                          self.grid_y * CELL_SIZE + CELL_SIZE//2)
                        break


class Score:
    """
    食べたクッキーの数をスコアとして表示するクラス
    """
    def __init__(self):
        self.font = pg.font.Font(None, 40)
        self.color = (255, 255, 255)
        self.value = 0
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.topleft = 10, 10

    def add(self, points: int):
        """スコアを加算"""
        self.value += points

    def update(self, screen: pg.Surface):
        """スコアを画面に表示"""
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        screen.blit(self.image, self.rect)


class Maze:
    """
    迷路とクッキーを管理するクラス
    """
    def __init__(self):
        """
        迷路データを初期化
        0:クッキー, 1:壁, 2:空, 3:外枠 ,5:ポータル
        """
        self.data = [
            [3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3],
            [3,2,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,3],
            [3,1,1,1,1,0,1,0,1,1,1,1,1,1,1,1,1,1,1,1,1,0,1,3],
            [3,0,1,1,1,0,1,0,0,0,0,0,0,0,0,0,0,1,1,1,0,0,1,3],
            [3,0,1,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,1,3],
            [3,0,1,0,0,1,1,1,1,1,0,1,0,1,1,1,1,1,0,1,0,1,1,3],
            [3,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,3],
            [3,1,1,1,1,0,1,0,1,1,1,0,1,1,1,0,0,1,1,1,1,1,1,3],
            [3,1,1,1,1,0,1,0,1,0,0,0,0,0,1,0,0,1,1,1,1,1,1,3],
            [3,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,3],
            [3,1,1,1,1,0,1,0,1,0,0,0,0,0,1,0,0,1,1,1,1,1,1,3],
            [3,1,1,1,1,0,1,0,1,1,1,1,1,1,1,0,0,1,1,1,1,1,1,3],
            [3,0,0,0,0,0,1,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,1,3],
            [3,1,1,0,0,1,1,1,1,1,0,1,0,1,1,1,1,1,0,1,1,1,1,3],
            [3,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,3],
            [3,1,1,0,0,1,1,0,1,1,1,1,1,1,1,0,1,1,0,1,1,0,1,3],
            [3,1,1,0,0,0,1,0,0,0,0,0,0,0,0,0,1,1,0,1,1,0,1,3],
            [3,0,0,0,0,0,0,0,0,0,0,1,0,1,1,0,1,1,0,0,0,0,1,3],
            [3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3],
            [3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3]
        ]
        self.wall_color = (0, 0, 255)
        self.cookie_color = (255, 255, 0)

    def draw(self, screen: pg.Surface):
        """迷路とクッキーを描画"""
        for y in range(len(self.data)):
            for x in range(len(self.data[y])):
                if self.data[y][x] == 1 or self.data[y][x] == 3:
                    # 壁を描画
                    pg.draw.rect(screen, self.wall_color, 
                               (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE))
                elif self.data[y][x] == 0:
                    # クッキーを描画
                    pg.draw.circle(screen, self.cookie_color,
                                 (x * CELL_SIZE + CELL_SIZE//2, y * CELL_SIZE + CELL_SIZE//2), 3)

    def count_cookies(self) -> int:
        """残りのクッキー数をカウント"""
        count = 0
        for row in self.data:
            count += row.count(0)
        return count


def main():
    pg.display.set_caption("こうかまん")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_color = (0, 0, 0)
    
    maze = Maze()
    score = Score()
    koukaman = Pacman(maze.data, (1, 1))
    enemies = pg.sprite.Group()
    enemies.add(Enemy(maze.data, (10, 10), "かまトゥ.png"))
    enemies.add(Enemy(maze.data, (12, 10), "ぱっちぃ.png"))
    
    koukaman_group = pg.sprite.GroupSingle(koukaman)

    tmr = 0
    clock = pg.time.Clock()
    
    while True:
        key_lst = pg.key.get_pressed()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return 0
        
        screen.fill(bg_color)
        maze.draw(screen)
        
        # こうかまんがクッキーを食べたらスコア加算
        if maze.data[koukaman.grid_y][koukaman.grid_x] == 2:
            score.add(10)
        
        # 敵との衝突判定
        for enemy in enemies:
            if koukaman.grid_x == enemy.grid_x and koukaman.grid_y == enemy.grid_y:
                # ゲームオーバー
                font = pg.font.Font(None, 80)
                text = font.render("GAME OVER", True, (255, 0, 0))
                text_rect = text.get_rect(center=(WIDTH//2, HEIGHT//2))
                screen.blit(text, text_rect)
                pg.display.update()
                time.sleep(3)
                return
        
        # クリア判定
        if maze.count_cookies() == 0:
            font = pg.font.Font(None, 80)
            text = font.render("CLEAR!", True, (0, 255, 0))
            text_rect = text.get_rect(center=(WIDTH//2, HEIGHT//2))
            screen.blit(text, text_rect)
            pg.display.update()
            time.sleep(3)
            return
        
        koukaman.update(key_lst, screen)
        enemies.update()
        enemies.draw(screen)
        score.update(screen)
        
        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()