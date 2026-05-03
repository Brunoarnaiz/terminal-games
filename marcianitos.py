#!/usr/bin/env python3
"""
Marcianitos - Space Invaders en la terminal
Controles: ← → mover, SPACE disparar, P pausa, Q salir
"""

import curses
import random
import os

SAVE_FILE = os.path.expanduser("~/.cache/marcianitos.score")

def load_score():
    try:
        with open(SAVE_FILE) as f:
            return int(f.read().strip())
    except Exception:
        return 0

def save_score(s):
    try:
        os.makedirs(os.path.dirname(SAVE_FILE), exist_ok=True)
        with open(SAVE_FILE, "w") as f:
            f.write(str(s))
    except Exception:
        pass

# ── Title Screen ──────────────────────────────────────────────

def show_title(scr):
    curses.curs_set(0)
    scr.nodelay(True)
    scr.keypad(True)
    curses.start_color()
    curses.use_default_colors()
    for i in range(1, 7):
        curses.init_pair(i, i, -1)

    h, w = scr.getmaxyx()
    stars = [(random.randint(1, h-2), random.randint(1, w-2)) for _ in range(40)]
    frame = 0

    while True:
        scr.clear()
        # Stars
        for sy, sx in stars:
            if random.random() < 0.05:
                continue
            ch = random.choice([".", "·", "*", "+"])
            col = random.choice([3, 4, 6, 5])
            try:
                scr.addstr(sy, sx, ch, curses.color_pair(col))
            except curses.error:
                pass

        # Border
        try:
            scr.addstr(0, 0, "╔" + "═" * (w - 2) + "╗", curses.color_pair(6))
            for y in range(1, h - 1):
                scr.addstr(y, 0, "║", curses.color_pair(6))
                scr.addstr(y, w - 1, "║", curses.color_pair(6))
            scr.addstr(h - 1, 0, "╚" + "═" * (w - 2) + "╝", curses.color_pair(6))
        except curses.error:
            pass

        # Title
        title = [
            "  ██╗   ██╗ █████╗ ██████╗  ██████╗██╗ █████╗ ███╗   ██╗██╗████████╗ ██████╗ ███████╗  ",
            "  ██║   ██║██╔══██╗██╔══██╗██╔════╝██║██╔══██╗████╗  ██║██║╚══██╔══╝██╔═══██╗██╔════╝  ",
            "  ██║   ██║███████║██████╔╝██║     ██║███████║██╔██╗ ██║██║   ██║   ██║   ██║███████╗  ",
            "  ╚██╗ ██╔╝██╔══██║██╔══██╗██║     ██║██╔══██║██║╚██╗██║██║   ██║   ██║   ██║╚════██║  ",
            "   ╚████╔╝ ██║  ██║██║  ██║╚██████╗██║██║  ██║██║ ╚████║██║   ██║   ╚██████╔╝███████║  ",
            "    ╚═══╝  ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝   ╚═╝    ╚═════╝ ╚══════╝  ",
        ]
        th = len(title)
        tw = len(title[0]) if title else 0
        ty = max(3, h // 2 - th // 2 - 2)
        tx = max(1, (w - tw) // 2)
        for i, line in enumerate(title):
            try:
                col = 2 if i < 2 else (4 if i < 4 else 1)
                scr.addstr(ty + i, tx, line[:w-2], curses.color_pair(col) | curses.A_BOLD)
            except curses.error:
                pass

        # Controls
        msgs = [
            ("CONTROLES", 6),
            ("", 1),
            ("← →  o  A D    Mover nave", 5),
            ("SPACE          Disparar", 5),
            ("P              Pausa", 5),
            ("Q              Salir", 5),
            ("", 1),
        ]
        cy = ty + th + 2
        for text, col in msgs:
            if text:
                try:
                    scr.addstr(cy, max(1, (w - len(text)) // 2), text[:w-2], curses.color_pair(col) | (curses.A_BOLD if col == 6 else 0))
                except curses.error:
                    pass
            cy += 1

        # Blinking prompt
        if (frame // 10) % 2 == 0:
            prompt = "  >>  PULSA ESPACIO PARA EMPEZAR  <<  "
            try:
                scr.addstr(h - 3, max(1, (w - len(prompt)) // 2), prompt[:w-2],
                           curses.color_pair(3) | curses.A_BOLD | curses.A_REVERSE)
            except curses.error:
                pass

        scr.refresh()
        curses.napms(40)
        frame += 1

        k = scr.getch()
        if k == ord(' '):
            break
        if k in (ord('q'), ord('Q')):
            return False
    return True

# ── Game ──────────────────────────────────────────────────────

def main(stdscr):
    if not show_title(stdscr):
        return

    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.keypad(True)
    for i in range(1, 7):
        curses.init_pair(i, i, -1)

    h, w = stdscr.getmaxyx()
    if h < 20 or w < 50:
        stdscr.nodelay(False)
        stdscr.clear()
        msg = "Terminal muy pequeña. Min: 50x20"
        stdscr.addstr(h//2, max(0, (w-len(msg))//2), msg, curses.A_BOLD)
        stdscr.refresh()
        stdscr.getch()
        return

    score = 0
    high = load_score()
    wave = 1
    lives = 3
    px = w // 2
    py = h - 2
    cooldown = 0
    rapid = 0
    shield = False

    bullets = []
    ebullets = []
    enemies = []
    barriers = []
    particles = []
    powerups = []
    spawning = []
    spawn_timer = 0

    enemy_dir = 1
    enemy_spd = 0.3
    enemy_t = 0
    shoot_t = 0
    shake = 0
    state = "play"
    stimer = 0

    def spawn_wave():
        nonlocal spawning, spawn_timer
        enemies.clear()
        spawning.clear()
        rows = min(2 + wave, 5)
        cols = min(6 + wave, 10)
        sx = max(3, (w - cols * 3) // 2)
        for r in range(rows):
            ch = ["M", "A", "R", "X", "Z"][min(r, 4)]
            sc = (r + 1) * 10
            for c in range(cols):
                spawning.append({"x": sx + c*3, "y": 3 + r*2, "ch": ch, "sc": sc, "dead": False})
        spawn_timer = 0

    def spawn_barriers():
        barriers.clear()
        n = 4
        step = w // (n + 1)
        for i in range(n):
            bx = step*(i+1) - 2
            by = h - 4
            for dx in range(5):
                for dy in range(2):
                    barriers.append({"x": bx+dx, "y": by+dy, "hp": 3, "dead": False})

    def add_particles(x, y, col):
        for _ in range(6):
            particles.append({"x": x, "y": y, "vx": random.uniform(-0.6, 0.6),
                              "vy": random.uniform(-0.6, 0.6), "life": random.randint(5, 10),
                              "ch": random.choice(["*", "+", "."]), "col": col})

    spawn_wave()
    spawn_barriers()

    while True:
        key = stdscr.getch()

        if state == "pause":
            if key in (ord('p'), ord('P')):
                state = "play"
            elif key in (ord('q'), ord('Q')):
                save_score(max(score, high))
                return
            stdscr.clear()
            m = " PAUSA - P para continuar "
            stdscr.addstr(h//2, max(0, (w-len(m))//2), m, curses.A_BOLD | curses.A_REVERSE)
            stdscr.refresh()
            curses.napms(50)
            continue

        if state == "waveclear":
            stimer -= 1
            if stimer <= 0:
                wave += 1
                enemy_spd = min(0.3 + wave*0.07, 1.6)
                spawn_wave()
                spawn_barriers()
                if wave % 3 == 0:
                    lives = min(lives + 1, 5)
                state = "play"
            else:
                stdscr.clear()
                m = f" OLEADA {wave} COMPLETADA "
                stdscr.addstr(h//2, max(0, (w-len(m))//2), m, curses.color_pair(2) | curses.A_BOLD | curses.A_REVERSE)
                stdscr.refresh()
                curses.napms(50)
                continue

        if state == "gameover":
            stdscr.clear()
            lines = [
                (" GAME OVER ", 4, curses.A_BOLD | curses.A_REVERSE),
                (f" Score: {score} ", 5, 0),
                (f" Record: {max(score, high)} ", 3, 0),
                ("", 1, 0),
                (" R - Reintentar ", 1, 0),
                (" Q - Salir ", 1, 0),
            ]
            y = h//2 - 3
            for text, col, attr in lines:
                if text:
                    stdscr.addstr(y, max(0, (w-len(text))//2), text, curses.color_pair(col) | attr)
                y += 1
            stdscr.refresh()
            stdscr.nodelay(False)
            while True:
                k = stdscr.getch()
                if k in (ord('r'), ord('R')):
                    score = 0; wave = 1; lives = 3; px = w//2; rapid = 0; shield = False
                    bullets.clear(); ebullets.clear(); particles.clear(); powerups.clear()
                    enemy_dir = 1; enemy_spd = 0.3; enemy_t = 0; state = "play"
                    spawn_wave(); spawn_barriers()
                    stdscr.nodelay(True)
                    break
                elif k in (ord('q'), ord('Q')):
                    save_score(max(score, high))
                    return
            continue

        # ── Spawning animation ──
        if spawning:
            spawn_timer += 1
            if spawn_timer >= 3:
                spawn_timer = 0
                enemies.append(spawning.pop(0))

        # ── Input ──
        if key == curses.KEY_LEFT or key in (ord('a'), ord('A')):
            px = max(1, px - 1)
        elif key == curses.KEY_RIGHT or key in (ord('d'), ord('D')):
            px = min(w - 2, px + 1)
        elif key == ord(' '):
            if cooldown <= 0 and not spawning:
                bullets.append({"x": px, "y": py - 1, "dead": False})
                if rapid > 0:
                    bullets.append({"x": px-1, "y": py-1, "dead": False})
                    bullets.append({"x": px+1, "y": py-1, "dead": False})
                cooldown = 5 if rapid > 0 else 10
        elif key in (ord('p'), ord('P')):
            state = "pause"
            continue
        elif key in (ord('q'), ord('Q')):
            save_score(max(score, high))
            return

        if cooldown > 0:
            cooldown -= 1
        if rapid > 0:
            rapid -= 1

        # ── Enemies move (only after spawn done) ──
        if not spawning:
            enemy_t += enemy_spd
            if enemy_t >= 1:
                enemy_t = 0
                edge = any((not e["dead"] and (e["x"] <= 1 or e["x"] >= w-2)) for e in enemies)
                if edge:
                    enemy_dir *= -1
                    for e in enemies:
                        e["y"] += 1
                    shake = 3
                else:
                    for e in enemies:
                        e["x"] += enemy_dir

        # ── Enemy shoot ──
        shoot_t += 1
        if shoot_t >= max(20, 55 - wave*4):
            shoot_t = 0
            alive = [e for e in enemies if not e["dead"]]
            if alive:
                cols = {}
                for e in alive:
                    c = e["x"] // 3
                    if c not in cols or e["y"] > cols[c]["y"]:
                        cols[c] = e
                shooters = list(cols.values())
                for s in random.sample(shooters, min(len(shooters), 1 + wave//3)):
                    if random.random() < 0.4:
                        ebullets.append({"x": s["x"], "y": s["y"] + 1, "dead": False})

        # ── Move bullets ──
        for b in bullets:
            b["y"] -= 1
            if b["y"] < 2:
                b["dead"] = True
        for b in ebullets:
            b["y"] += 1
            if b["y"] >= h - 1:
                b["dead"] = True

        # ── Move powerups ──
        for p in powerups:
            p["y"] += 0.4
            if p["y"] >= h - 1:
                p["dead"] = True

        # ── Particles ──
        for p in particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["life"] -= 1
        particles = [p for p in particles if p["life"] > 0]

        # ── Collisions ──
        for b in bullets:
            if b["dead"]:
                continue
            for e in enemies:
                if e["dead"]:
                    continue
                if abs(b["x"] - e["x"]) <= 1 and abs(b["y"] - e["y"]) <= 1:
                    b["dead"] = True
                    e["dead"] = True
                    score += e["sc"]
                    add_particles(e["x"], e["y"], 4)
                    if random.random() < 0.12:
                        t = random.choice([("+", 4, "life"), (">>", 3, "rapid"), ("O", 6, "shield")])
                        powerups.append({"x": e["x"], "y": e["y"], "ch": t[0], "col": t[1], "ptype": t[2], "dead": False})
                    break
            if not b["dead"]:
                for bar in barriers:
                    if bar["dead"]:
                        continue
                    if round(b["x"]) == bar["x"] and round(b["y"]) == bar["y"]:
                        b["dead"] = True
                        bar["hp"] -= 1
                        if bar["hp"] <= 0:
                            bar["dead"] = True
                            add_particles(bar["x"], bar["y"], 6)
                        break

        for b in ebullets:
            if b["dead"]:
                continue
            if abs(b["x"] - px) <= 1 and abs(b["y"] - py) <= 1:
                b["dead"] = True
                if shield:
                    shield = False
                    add_particles(px, py, 6)
                else:
                    lives -= 1
                    shake = 5
                    add_particles(px, py, 2)
                    if lives <= 0:
                        state = "gameover"
                        save_score(max(score, high))
                break
            for bar in barriers:
                if bar["dead"]:
                    continue
                if round(b["x"]) == bar["x"] and round(b["y"]) == bar["y"]:
                    b["dead"] = True
                    bar["hp"] -= 1
                    if bar["hp"] <= 0:
                        bar["dead"] = True
                    break

        for p in powerups:
            if p["dead"]:
                continue
            if abs(p["x"] - px) <= 1 and abs(p["y"] - py) <= 1:
                p["dead"] = True
                if p["ptype"] == "life":
                    lives = min(lives + 1, 5)
                    score += 50
                elif p["ptype"] == "rapid":
                    rapid = 120
                    score += 30
                elif p["ptype"] == "shield":
                    shield = True
                    score += 30
                add_particles(p["x"], p["y"], p["col"])
                break

        # Enemies bottom
        for e in enemies:
            if not e["dead"] and e["y"] >= h - 2:
                state = "gameover"
                save_score(max(score, high))
                break

        # Cleanup
        bullets = [b for b in bullets if not b["dead"]]
        ebullets = [b for b in ebullets if not b["dead"]]
        enemies = [e for e in enemies if not e["dead"]]
        powerups = [p for p in powerups if not p["dead"]]

        if not enemies and not spawning and state == "play":
            state = "waveclear"
            stimer = 50
            score += wave * 100

        if shake > 0:
            shake -= 1

        # ── Render ──
        stdscr.clear()
        ox = random.randint(-shake, shake) if shake else 0
        oy = random.randint(-shake, shake) if shake else 0

        def put(y, x, ch, col=5, attr=0):
            try:
                yy = int(y) + oy
                xx = int(x) + ox
                if 0 <= yy < h and 0 <= xx < w:
                    stdscr.addstr(yy, xx, ch, curses.color_pair(col) | attr)
            except Exception:
                pass

        # HUD
        left = f" SCORE:{score:05d}  HIGH:{max(score,high):05d} "
        right = f" WAVE:{wave}  LIVES:{'@'*lives}{' '*max(0,5-lives)} "
        mid = " " * max(1, w - len(left) - len(right) - 2)
        put(0, 0, left + mid + right, 5, curses.A_BOLD)
        put(1, 0, "-" * (w - 1), 4)

        if rapid > 0:
            put(0, w//2 - 5, " RAPID ", 3, curses.A_BOLD | curses.A_REVERSE)
        if shield:
            put(0, w//2 + 2, " SHIELD ", 6, curses.A_BOLD | curses.A_REVERSE)

        # Barriers
        for b in barriers:
            if not b["dead"]:
                ch = ["#", "=", "-"][max(0, 2-b["hp"])]
                put(b["y"], b["x"], ch, 6)

        # Enemies
        for e in enemies:
            put(e["y"], e["x"], e["ch"], 2, curses.A_BOLD)

        # Bullets
        for b in bullets:
            put(b["y"], b["x"], "|", 3)
        for b in ebullets:
            put(b["y"], b["x"], "v", 4)

        # Powerups
        for p in powerups:
            put(p["y"], p["x"], p["ch"], p["col"], curses.A_BOLD)

        # Player
        pch = "^" if not shield else "O"
        put(py, px, pch, 2, curses.A_BOLD)

        # Particles
        for p in particles:
            put(p["y"], p["x"], p["ch"], p["col"])

        stdscr.refresh()
        curses.napms(40)

if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
    print("\n  Hasta la proxima!")
