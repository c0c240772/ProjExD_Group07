import os
import random
import sys
import time
import pygame as pg


WIDTH = 720  # ゲームウィンドウの幅
HEIGHT = 570  # ゲームウィンドウの高さ
CELL_SIZE = 30  # セルサイズ
os.chdir(os.path.dirname(os.path.abspath(__file__)))


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
        # 画像読み込み（エラー回避）
        try:
            img = pg.transform.rotozoom(pg.image.load(f"fig/2.png"), 0, 0.9)
            self.image = pg.transform.flip(img, True, False)
        except FileNotFoundError:
            self.image = pg.Surface((CELL_SIZE, CELL_SIZE))
            self.image.fill((255, 0, 0))

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

        
        # 追加機能用フラグ：吸い込みスキルは1回のみ
        self.has_suction = True
        # 吸い込みエフェクト用タイマー
        self.suction_timer = 0
        self.move_interval_ms = 120
        self.last_move_time = 0
    
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
        # 吸い込みエフェクト描画
        if self.suction_timer > 0:
            pg.draw.circle(screen, (0, 255, 255), self.rect.center, 3.5 * CELL_SIZE, 5)
            self.suction_timer -= 1

        if not self.can_move_now():
            screen.blit(self.image, self.rect)
            return
        
        for k, mv in self.delta.items():
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
                break
        
        screen.blit(self.image, self.rect)

    # ----------------------------------------------------
    # 追加機能：吸い込みスキル（担当：渡辺）
    # 条件：7x7マス、エフェクト表示、1回のみ
    # ----------------------------------------------------
    def suck_cookies(self):
        """
        周囲のクッキーを吸い込む
        戻り値：吸い込んだ（食べた）クッキーの数
        """
        # すでに使用済みなら何もしない
        if not self.has_suction:
            return 0
            
        suck_range = 3  # 半径3マス（中心含め7x7）
        eaten_count = 0
        
        # エフェクト表示時間をセット（30フレーム）
        self.suction_timer = 30

        # 範囲内のマスを走査
        for dy in range(-suck_range, suck_range + 1):
            for dx in range(-suck_range, suck_range + 1):
                tx, ty = self.grid_x + dx, self.grid_y + dy
                
                # 迷路の範囲内チェック
                if 0 <= ty < len(self.maze) and 0 <= tx < len(self.maze[0]):
                    # クッキー(0)があれば食べる
                    if self.maze[ty][tx] == 0:
                        self.maze[ty][tx] = 2  # 空にする
                        eaten_count += 1
        
        # 使用済みフラグを立てる（以降使えない）
        self.has_suction = False
        return eaten_count
    # ----------------------------------------------------


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
        try:
            img = pg.image.load(f"fig/{img_name}")
            self.image = pg.transform.rotozoom(img, 0, 0.1) 
        except FileNotFoundError:
            self.image = pg.Surface((CELL_SIZE, CELL_SIZE))
            self.image.fill((0, 0, 255))

        self.rect = self.image.get_rect()
        self.grid_x, self.grid_y = xy
        self.rect.center = (self.grid_x * CELL_SIZE + CELL_SIZE//2,
                           self.grid_y * CELL_SIZE + CELL_SIZE//2)
        self.move_timer = 0
        self.move_interval = 10
        self.is_stopped = False  # 停止フラグ

    def update(self):
        """
        敵をランダムに移動させる（停止中は動かない）
        """
        if self.is_stopped:  # 停止中は移動しない
            return
            
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

class Warp:
    """
    画面の端に行くと反対側に出てくるワープに関するクラス
    """
    def __init__(self, maze):
        self.maze = maze
        self.warp_row = 9  # ワープがある行
        self.left = 0
        self.right = 0

        # 左側のワープを探す
        for x in range(len(maze[self.warp_row])):
            if maze[self.warp_row][x] == 5:
                self.left = x
                break

        # 右側のワープを探す
        for x in range(len(maze[self.warp_row]) - 1, -1, -1):
            if maze[self.warp_row][x] == 5:
                self.right = x
                break

    def check_and_warp(self, pacman):
        # ワープの行にいるときだけ判定
        if pacman.grid_y == self.warp_row:

            # 左端に来たら右側へ
            if pacman.grid_x == self.left:
                pacman.grid_x = self.right - 1

            # 右端に来たら左側へ
            elif pacman.grid_x == self.right: 
                pacman.grid_x = self.left + 1

            pacman.rect.center = (
                pacman.grid_x * CELL_SIZE + CELL_SIZE // 2,
                pacman.grid_y * CELL_SIZE + CELL_SIZE // 2
            )

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
        0:クッキー, 1:壁, 2:空, 3:外枠, 4:時を止めるアイテム
        """
        self.data = [
            [3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3],
            [3,2,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,3],
            [3,1,1,1,1,0,1,0,1,1,1,1,1,1,1,1,1,1,1,1,1,0,1,3],
            [3,0,1,1,1,0,1,0,0,0,0,0,0,0,0,0,0,1,1,1,0,0,1,3],
            [3,0,1,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,1,3],
            [3,0,1,0,0,1,1,1,1,1,0,1,0,1,1,1,1,1,0,1,0,1,1,3],
            [3,0,0,0,4,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,3],
            [3,1,1,1,1,0,1,0,1,1,1,0,1,1,1,0,0,1,1,1,1,1,1,3],
            [3,1,1,1,1,0,1,0,1,0,0,0,0,0,1,0,0,1,1,1,1,1,1,3],
            [5,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,5],
            [3,1,1,1,1,0,1,0,1,0,0,0,0,0,1,0,0,1,1,1,1,1,1,3],
            [3,1,1,1,1,0,1,0,1,1,1,1,1,1,1,0,0,1,1,1,1,1,1,3],
            [3,0,0,0,0,0,1,0,0,0,0,1,0,0,0,0,0,0,4,0,0,0,1,3],
            [3,1,1,0,0,1,1,1,1,1,0,1,0,1,1,1,1,1,0,1,1,1,1,3],
            [3,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,3],
            [3,1,1,0,0,1,1,0,1,1,1,1,1,1,1,0,1,1,0,1,1,0,1,3],
            [3,1,1,0,4,0,1,0,0,0,0,0,0,0,0,0,1,1,0,1,1,0,1,3],
            [3,0,0,0,0,0,0,0,0,0,0,1,0,1,1,0,1,1,0,0,0,0,1,3],
            [3,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3],
            [3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3]
        ]
        self.wall_color = (0, 0, 255)
        self.cookie_color = (255, 255, 0) 
        self.portal_color = (255, 255, 255)  # ポータルの色
        self.cookie_color = (255, 255, 0)
        # 時を止めるアイテムの画像を読み込む
        time_stop_img = pg.image.load("fig/時を止めるアイテム.png")
        self.time_stop_img = pg.transform.scale(time_stop_img, (CELL_SIZE, CELL_SIZE))

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
                elif self.data[y][x] == 5:
                    # ポータルを描画
                    pass  # ポータルは背景と同じ色で描画しない
                elif self.data[y][x] == 4:
                    # 時を止めるアイテムを画像で描画
                    screen.blit(self.time_stop_img, (x * CELL_SIZE, y * CELL_SIZE))

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
    # 敵の画像が手元にない場合エラーになるので、ファイル名を確認してください
    enemies.add(Enemy(maze.data, (10, 10), "かまトゥ.png"))
    enemies.add(Enemy(maze.data, (12, 10), "ぱっちぃ.png"))
    warp = Warp(maze.data)
    
    # 時を止める効果の管理
    time_stop_active = False
    time_stop_start = 0
    time_stop_duration = 5000  # 5秒間停止

    clock = pg.time.Clock()
    fry_count = 3
    
    while True:
        key_lst = pg.key.get_pressed()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return 0
            if event.type == pg.KEYDOWN and event.key == pg.K_d:  # Dキーが押されたら
                if score.value >= 300:  # スコア300以上だったら
                    score.add(-300)  # スコア300使用してダッシュ
                    koukaman.move_interval_ms = 10
            if event.type == pg.KEYUP and event.key == pg.K_d:  # Dキーが離されたら通常スピード
                koukaman.move_interval_ms = 120
        
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_f:
                    if  fry_count > 0:
                        koukaman.fry(screen)
                        fry_count -= 1
                    
        screen.fill(bg_color)
        maze.draw(screen)

        koukaman.update(key_lst, screen)
        warp.check_and_warp(koukaman)
        # こうかまんがクッキーを食べたらスコア加算
        if maze.data[koukaman.grid_y][koukaman.grid_x] == 0:
            score.add(10)
            maze.data[koukaman.grid_y][koukaman.grid_x] = 2
        
        # 時を止めるアイテムを取得した場合
        if maze.data[koukaman.grid_y][koukaman.grid_x] == 4:
            maze.data[koukaman.grid_y][koukaman.grid_x] = 2
            time_stop_active = True
            time_stop_start = pg.time.get_ticks()
            # すべての敵を停止
            for enemy in enemies:
                enemy.is_stopped = True
        
        # 時を止める効果の時間管理
        if time_stop_active:
            current_time = pg.time.get_ticks()
            if current_time - time_stop_start >= time_stop_duration:
                time_stop_active = False
                # すべての敵を再開
                for enemy in enemies:
                    enemy.is_stopped = False
        
        
        # --- 追加機能：吸い込みスキル（担当：渡辺） ---
        if key_lst[pg.K_s]:
            n = koukaman.suck_cookies()
            score.add(n * 10)
        # ----------------------------------------
        
        # # 通常の移動で食べたクッキーの加算
        # if maze.data[koukaman.grid_y][koukaman.grid_x] == 2:
        #     score.add(10)
        #     maze.data[koukaman.grid_y][koukaman.grid_x] = 2
        
        #         # --- 追加機能：吸い込みスキル（担当：渡辺） ---
        # if key_lst[pg.K_s]:
        #     n = koukaman.suck_cookies()
        #     score.add(n * 10)
        # # ----------------------------------------

                    
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
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()