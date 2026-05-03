#!/usr/bin/env python3
"""
Marcianitos - Space Invaders en la terminal
Requiere: Python 3 + terminal con soporte Unicode
Linux/Mac: funciona nativamente
Windows: pip install windows-curses

Controles:
  ← / →    Mover nave
  SPACE    Disparar
  Q        Salir
"""

import curses
import random
import time
import os

# ── Configuración ─────────────────────────────────────────────

REFRESH_MS = 50
PLAYER_SPEED = 2
BULLET_SPEED = 1
ENEMY_BULLET_SPEED = 1
INITIAL_ENEMY_SPEED = 0.3
ENEMY_DROP = 1

# ── Entidades ─────────────────────────────────────────────────

class Entity:
    def __init__(self, x, y, char, color_pair=1):
        self.x = x
        self.y = y
        self.char = char
        self.color_pair = color_pair
        self.dead = False

class Player(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, "▀", 2)
        self.lives = 3
        self.cooldown = 0

class Bullet(Entity):
    def __init__(self, x, y, direction=-1):
        super().__init__(x, y, "│", 3)
        self.direction = direction  # -1 arriba, +1 abajo

class Enemy(Entity):
    def __init__(self, x, y, row):
        chars = ["👾", "👽", "🛸"]
        super().__init__(x, y, chars[row % len(chars)], 4)
        self.score = (3 - row) * 10 + 10

class Explosion(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, "💥", 5)
        self.timer = 6

# ── Juego ─────────────────────────────────────────────────────

class Game:
    def __init__(self, stdscr):
        self.scr = stdscr
        self.setup_colors()
        self.reset()

    def setup_colors(self):
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_WHITE, -1)   # default
        curses.init_pair(2, curses.COLOR_GREEN, -1)   # player
        curses.init_pair(3, curses.COLOR_YELLOW, -1)  # bullets
        curses.init_pair(4, curses.COLOR_RED, -1)     # enemies
        curses.init_pair(5, curses.COLOR_MAGENTA, -1) # explosion
        curses.init_pair(6, curses.COLOR_CYAN, -1)    # hud
        curses.curs_set(0)
        self.scr.nodelay(True)
        self.scr.keypad(True)

    def reset(self):
        h, w = self.scr.getmaxyx()
        self.h, self.w = h, w
        self.player = Player(w // 2, h - 2)
        self.bullets = []
        self.enemy_bullets = []
        self.enemies = []
        self.explosions = []
        self.score = 0
        self.wave = 1
        self.enemy_dir = 1
        self.enemy_speed = INITIAL_ENEMY_SPEED
        self.enemy_timer = 0
        self.enemy_shoot_timer = 0
        self.game_over = False
        self.won_wave = False
        self.spawn_enemies()

    def spawn_enemies(self):
        self.enemies.clear()
        rows = min(2 + self.wave, 5)
        cols = min(6 + self.wave, 10)
        start_x = max(2, (self.w - cols * 3) // 2)
        for r in range(rows):
            for c in range(cols):
                ex = start_x + c * 3
                ey = 2 + r * 2
                self.enemies.append(Enemy(ex, ey, r))

    def draw(self):
        self.scr.clear()
        h, w = self.h, self.w

        # HUD
        hud = f"  PUNTUACIÓN: {self.score}   OLEADA: {self.wave}   VIDAS: {'♥' * self.player.lives}  "
        self.scr.addstr(0, 0, hud[:w-1], curses.color_pair(6) | curses.A_BOLD)

        # Línea divisoria
        try:
            self.scr.addstr(1, 0, "─" * (w - 1), curses.color_pair(6))
        except curses.error:
            pass

        # Enemigos
        for e in self.enemies:
            if not e.dead:
                try:
                    self.scr.addstr(int(e.y), int(e.x), e.char, curses.color_pair(e.color_pair))
                except curses.error:
                    pass

        # Balas
        for b in self.bullets + self.enemy_bullets:
            if not b.dead:
                try:
                    self.scr.addstr(int(b.y), int(b.x), b.char, curses.color_pair(b.color_pair))
                except curses.error:
                    pass

        # Jugador
        try:
            self.scr.addstr(int(self.player.y), int(self.player.x), self.player.char,
                            curses.color_pair(self.player.color_pair) | curses.A_BOLD)
        except curses.error:
            pass

        # Explosiones
        for ex in self.explosions:
            try:
                self.scr.addstr(int(ex.y), int(ex.x), ex.char, curses.color_pair(ex.color_pair))
            except curses.error:
                pass

        # Mensajes
        if self.won_wave:
            msg = "  OLEADA COMPLETADA  "
            mx = max(0, (w - len(msg)) // 2)
            my = h // 2
            try:
                self.scr.addstr(my, mx, msg, curses.color_pair(2) | curses.A_BOLD | curses.A_REVERSE)
            except curses.error:
                pass

        if self.game_over:
            msg1 = "  GAME OVER  "
            msg2 = f"  Puntuación final: {self.score}  "
            msg3 = "  [R]eintentar  [Q]uit  "
            my = h // 2 - 1
            try:
                self.scr.addstr(my, max(0, (w - len(msg1)) // 2), msg1,
                                curses.color_pair(4) | curses.A_BOLD | curses.A_REVERSE)
                self.scr.addstr(my + 1, max(0, (w - len(msg2)) // 2), msg2, curses.color_pair(6))
                self.scr.addstr(my + 3, max(0, (w - len(msg3)) // 2), msg3, curses.color_pair(1))
            except curses.error:
                pass

        self.scr.refresh()

    def update(self, key):
        if self.game_over:
            if key in (ord('r'), ord('R')):
                self.reset()
            return

        if self.won_wave:
            self.won_wave_timer -= 1
            if self.won_wave_timer <= 0:
                self.wave += 1
                self.enemy_speed = min(INITIAL_ENEMY_SPEED + self.wave * 0.08, 1.5)
                self.spawn_enemies()
                self.won_wave = False
            return

        h, w = self.h, self.w

        # ── Input ──
        if key == curses.KEY_LEFT or key == ord('a') or key == ord('A'):
            self.player.x = max(0, self.player.x - PLAYER_SPEED)
        elif key == curses.KEY_RIGHT or key == ord('d') or key == ord('D'):
            self.player.x = min(w - 1, self.player.x + PLAYER_SPEED)
        elif key == ord(' '):
            if self.player.cooldown <= 0:
                self.bullets.append(Bullet(self.player.x, self.player.y - 1, -1))
                self.player.cooldown = 8
        elif key in (ord('q'), ord('Q')):
            self.game_over = True
            self.score = -1  # señal de salida
            return

        if self.player.cooldown > 0:
            self.player.cooldown -= 1

        # ── Movimiento enemigos ──
        self.enemy_timer += self.enemy_speed
        if self.enemy_timer >= 1:
            self.enemy_timer = 0
            move_down = False
            for e in self.enemies:
                if not e.dead:
                    if e.x <= 1 or e.x >= w - 2:
                        move_down = True
                        break

            if move_down:
                self.enemy_dir *= -1
                for e in self.enemies:
                    e.y += ENEMY_DROP
            else:
                for e in self.enemies:
                    e.x += self.enemy_dir

        # ── Disparos enemigos ──
        self.enemy_shoot_timer += 1
        if self.enemy_shoot_timer >= max(20, 60 - self.wave * 5):
            self.enemy_shoot_timer = 0
            alive = [e for e in self.enemies if not e.dead]
            if alive:
                shooter = random.choice(alive)
                self.enemy_bullets.append(Bullet(shooter.x, shooter.y + 1, 1))

        # ── Mover balas ──
        for b in self.bullets:
            b.y += b.direction
            if b.y < 2:
                b.dead = True

        for b in self.enemy_bullets:
            b.y += b.direction
            if b.y >= h - 1:
                b.dead = True

        # ── Colisiones bala jugador vs enemigo ──
        for b in self.bullets:
            if b.dead:
                continue
            for e in self.enemies:
                if e.dead:
                    continue
                if abs(b.x - e.x) <= 1 and abs(b.y - e.y) <= 1:
                    b.dead = True
                    e.dead = True
                    self.score += e.score
                    self.explosions.append(Explosion(e.x, e.y))
                    break

        # ── Colisiones bala enemigo vs jugador ──
        for b in self.enemy_bullets:
            if b.dead:
                continue
            if abs(b.x - self.player.x) <= 1 and abs(b.y - self.player.y) <= 1:
                b.dead = True
                self.player.lives -= 1
                self.explosions.append(Explosion(self.player.x, self.player.y))
                if self.player.lives <= 0:
                    self.game_over = True
                break

        # ── Enemigos llegan abajo ──
        for e in self.enemies:
            if not e.dead and e.y >= h - 2:
                self.game_over = True
                break

        # ── Limpiar muertos ──
        self.bullets = [b for b in self.bullets if not b.dead]
        self.enemy_bullets = [b for b in self.enemy_bullets if not b.dead]
        self.enemies = [e for e in self.enemies if not e.dead]

        # ── Explosiones timer ──
        for ex in self.explosions:
            ex.timer -= 1
        self.explosions = [ex for ex in self.explosions if ex.timer > 0]

        # ── Victoria de oleada ──
        if not self.enemies and not self.won_wave:
            self.won_wave = True
            self.won_wave_timer = 40

# ── Pantallas ─────────────────────────────────────────────────

def show_title(stdscr):
    stdscr.clear()
    h, w = stdscr.getmaxyx()
    title = [
        "  ███╗   ███╗ █████╗ ██████╗  ██████╗██╗ █████╗ ███╗   ██╗██╗████████╗ ██████╗ ███████╗  ",
        "  ████╗ ████║██╔══██╗██╔══██╗██╔════╝██║██╔══██╗████╗  ██║██║╚══██╔══╝██╔═══██╗██╔════╝  ",
        "  ██╔████╔██║███████║██████╔╝██║     ██║███████║██╔██╗ ██║██║   ██║   ██║   ██║███████╗  ",
        "  ██║╚██╔╝██║██╔══██║██╔══██╗██║     ██║██╔══██║██║╚██╗██║██║   ██║   ██║   ██║╚════██║  ",
        "  ██║ ╚═╝ ██║██║  ██║██║  ██║╚██████╗██║██║  ██║██║ ╚████║██║   ██║   ╚██████╔╝███████║  ",
        "  ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝   ╚═╝    ╚═════╝ ╚══════╝  ",
    ]
    start_y = max(2, h // 2 - 6)
    start_x = max(0, (w - len(title[0])) // 2)
    for i, line in enumerate(title):
        try:
            stdscr.addstr(start_y + i, start_x, line[:w-1], curses.color_pair(4) | curses.A_BOLD)
        except curses.error:
            pass

    msgs = [
        ("  CONTROLES  ", 6),
        ("  ← →  Mover nave", 1),
        ("  SPACE  Disparar", 1),
        ("  Q  Salir", 1),
        ("", 1),
        ("  Presiona ENTER para empezar...  ", 2),
    ]
    y = start_y + len(title) + 2
    for text, color in msgs:
        try:
            stdscr.addstr(y, max(0, (w - len(text)) // 2), text[:w-1], curses.color_pair(color))
        except curses.error:
            pass
        y += 1

    stdscr.refresh()
    stdscr.nodelay(False)
    while stdscr.getch() not in (10, 13, curses.KEY_ENTER):
        pass
    stdscr.nodelay(True)

# ── Main ──────────────────────────────────────────────────────

def main(stdscr):
    show_title(stdscr)
    game = Game(stdscr)

    while True:
        key = stdscr.getch()
        game.update(key)
        game.draw()

        if game.game_over and game.score == -1:
            break

        if game.game_over:
            # esperar input en game over
            stdscr.nodelay(False)
            while True:
                k = stdscr.getch()
                if k in (ord('r'), ord('R')):
                    stdscr.nodelay(True)
                    game.reset()
                    break
                elif k in (ord('q'), ord('Q')):
                    return
            continue

        curses.napms(REFRESH_MS)

if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
    print("\n  ¡Hasta la próxima, piloto!")
