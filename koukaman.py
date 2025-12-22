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
        self.move_interval_ms = 120
        self.last_move_time = 0
        self.direction = (1,0)
        self.fry_cooldown = 200
        self.last_fry = -200
        self.fry_count = 3
        icon_6 = pg.image.load("fig/6.png")
        self.fry_icon = pg.transform.smoothscale(icon_6, (24, 24))
        self.fry_icon_margin = 10
        self.fry_icon_spacing = 8

    def can_move_now(self) -> bool:
        now = pg.time.get_ticks()
        if now - self.last_move_time >= self.move_interval_ms:
            self.last_move_time = now
            return True
        return False
    
    def fry(self,screen:pg.Surface):
        """
        こうかとんが飛行する関数
        引数1 screen:画面Surface
        """
        now = pg.time.get_ticks() # 現在フレームを取得
        if now - self.last_fry < self.fry_cooldown: # 飛行のクールタイムより短かったら
            screen.blit(self.image, self.rect)
            return
        self.last_fry = now # 飛行時間を更新

        origin_x, origin_y = self.grid_x, self.grid_y # 元の位置を記憶
        dx, dy = self.direction # 動く方向を記憶
        target_x = self.grid_x + dx*2
        target_y = self.grid_y + dy*2
        
        row = len(self.maze)         # 行数
        columns = len(self.maze[0])      # 列数

        if not (0 <= target_y < row and 0 <= target_x < columns): # 2マス先が範囲外なら元の位置に戻す
            self.grid_x, self.grid_y = origin_x, origin_y
        else:
            while True: # 壁以外まで移動
                cell = self.maze[target_y][target_x]
                if cell in (1, 3):  # 壁なら一マス追加
                    target_x += dx
                    target_y += dy
                    if not (0 <= target_y < row and 0 <= target_x < columns): # 範囲外に出たら元の位置に戻る
                        self.grid_x, self.grid_y = origin_x, origin_y
                        break
                    continue
                self.grid_x, self.grid_y = target_x, target_y # 更新する位置の設定
                break
        self.fry_count -= 1
        self.rect.center = (self.grid_x * CELL_SIZE + CELL_SIZE // 2,
                            self.grid_y * CELL_SIZE + CELL_SIZE // 2)  
        # クッキーを食べる
        if self.maze[self.grid_y][self.grid_x] == 0:
            self.maze[self.grid_y][self.grid_x] = 2
        screen.blit(self.image, self.rect)
        
    def draw_fry_icons(self, screen: pg.Surface):
        """
        残り飛行回数を表示する関数
        引数1 screen:画面Surface
        """
        icon_w = self.fry_icon.get_width()
        icon_h = self.fry_icon.get_height()
        x = self.fry_icon_margin
        y = HEIGHT - self.fry_icon_margin - icon_h
        for i in range(self.fry_count):
            screen.blit(self.fry_icon, (x + i * (icon_w + self.fry_icon_spacing), y))

    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じてこうかまんを移動させる
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        """
        if not self.can_move_now():
            screen.blit(self.image, self.rect)
            return
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                new_grid_x = self.grid_x + mv[0]
                new_grid_y = self.grid_y + mv[1]
                self.direction = mv # 向きの設定
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
        0:クッキー, 1:壁, 2:空, 3:外枠
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
    fry_count = 3
    
    while True:
        key_lst = pg.key.get_pressed()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return 0
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_f:
                    if  fry_count > 0:
                        koukaman.fry(screen)
                        fry_count -= 1
                    
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
        koukaman.draw_fry_icons(screen)
        score.update(screen)
        
        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()