#!/usr/bin/env python3
"""config-manager - gestor de archivos de configuración con TUI curses"""

import curses
import json
import os
import subprocess
import sys
from pathlib import Path

DATA_FILE = Path.home() / ".config" / "config-manager" / "entries.json"


def load_entries():
    if DATA_FILE.exists():
        try:
            return json.loads(DATA_FILE.read_text())
        except Exception:
            return []
    return []


def save_entries(entries):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(entries, indent=2, ensure_ascii=False))


def open_with_codium(path):
    try:
        subprocess.Popen(["codium", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return f"Abriendo {path} con Codium..."
    except FileNotFoundError:
        return "Error: 'codium' no encontrado en PATH"


def draw_ui(stdscr, entries, query, selected, status_msg, mode, input_buf):
    curses.curs_set(0)
    stdscr.clear()

    # Colores
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_CYAN, -1)    # título / separadores
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_CYAN)  # seleccionado
    curses.init_pair(3, curses.COLOR_YELLOW, -1)  # atajos
    curses.init_pair(4, curses.COLOR_GREEN, -1)   # status ok
    curses.init_pair(5, curses.COLOR_RED, -1)     # status error
    curses.init_pair(6, curses.COLOR_WHITE, -1)

    H, W = stdscr.getmaxyx()
    LEFT_W = max(30, W // 3)
    RIGHT_W = W - LEFT_W - 3  # bordes

    filtered = [e for e in entries if query.lower() in e["name"].lower() or query.lower() in e["path"].lower()]

    # ── Marco exterior ────────────────────────────────────────────────────────
    # Línea superior
    stdscr.addstr(0, 0, "┌" + "─" * (W - 2) + "┐", curses.color_pair(1))
    # Línea inferior (barra de atajos)
    stdscr.addstr(H - 2, 0, "├" + "─" * (W - 2) + "┤", curses.color_pair(1))
    # Última fila: evitar escribir en (H-1, W-1) — curses lanza error ahí
    bottom = "└" + "─" * (W - 2) + "┘"
    try:
        stdscr.addstr(H - 1, 0, bottom)
    except curses.error:
        stdscr.addstr(H - 1, 0, bottom[:-1])  # ponytail: omitir último char

    # Divisor vertical
    for row in range(1, H - 2):
        stdscr.addstr(row, 0, "│", curses.color_pair(1))
        stdscr.addstr(row, LEFT_W + 1, "│", curses.color_pair(1))
        stdscr.addstr(row, W - 1, "│", curses.color_pair(1))

    # ── Panel izquierdo: búsqueda + lista ────────────────────────────────────
    # Campo de búsqueda
    search_display = ("> " + (input_buf if mode == "search" else query) + "_").ljust(LEFT_W - 1)
    stdscr.addstr(1, 1, search_display[:LEFT_W - 1], curses.color_pair(1))
    stdscr.addstr(2, 1, "─" * LEFT_W, curses.color_pair(1))

    # Entradas
    list_start_row = 3
    list_height = H - 5  # espacio disponible

    # Calcular scroll
    scroll_offset = 0
    if selected >= list_height:
        scroll_offset = selected - list_height + 1

    for i, entry in enumerate(filtered[scroll_offset:scroll_offset + list_height]):
        row = list_start_row + i
        if row >= H - 2:
            break
        real_i = i + scroll_offset
        name = entry["name"][:12].ljust(12)
        path_short = entry["path"]
        # acortar path para que quepa
        max_path = LEFT_W - 15
        if len(path_short) > max_path:
            path_short = "…" + path_short[-(max_path - 1):]
        line = f"  {name}  {path_short}"
        line = line[:LEFT_W - 1].ljust(LEFT_W - 1)
        if real_i == selected:
            stdscr.addstr(row, 1, line, curses.color_pair(2))
        else:
            stdscr.addstr(row, 1, line)

    # Si no hay entradas
    if not entries:
        stdscr.addstr(list_start_row, 1, "  (sin entradas)  ", curses.color_pair(3))
        stdscr.addstr(list_start_row + 1, 1, "  Presiona 'a' para añadir", curses.color_pair(3))
    elif not filtered:
        stdscr.addstr(list_start_row, 1, "  Sin resultados", curses.color_pair(3))

    # ── Panel derecho: detalle ────────────────────────────────────────────────
    rx = LEFT_W + 2

    if mode == "add_name":
        stdscr.addstr(1, rx, "[ Nuevo - Nombre ]", curses.color_pair(3))
        stdscr.addstr(3, rx, f"Nombre: {input_buf}_")
        stdscr.addstr(5, rx, "Enter para continuar, ESC cancelar")
    elif mode == "add_path":
        stdscr.addstr(1, rx, "[ Nuevo - Ruta ]", curses.color_pair(3))
        stdscr.addstr(3, rx, f"Ruta: {input_buf}_")
        stdscr.addstr(5, rx, "Tip: ruta absoluta o ~/ ...")
        stdscr.addstr(6, rx, "Enter para guardar, ESC cancelar")
    elif mode == "confirm_delete":
        stdscr.addstr(1, rx, "[ Confirmar eliminación ]", curses.color_pair(5))
        if filtered and selected < len(filtered):
            e = filtered[selected]
            stdscr.addstr(3, rx, f"¿Eliminar '{e['name']}'?")
            stdscr.addstr(5, rx, "s = sí    n/ESC = cancelar", curses.color_pair(3))
    else:
        # Vista normal: detalle del seleccionado
        stdscr.addstr(1, rx, "config-manager", curses.color_pair(1) | curses.A_BOLD)
        if filtered and selected < len(filtered):
            e = filtered[selected]
            stdscr.addstr(3, rx, f"Nombre: {e['name']}", curses.A_BOLD)
            # ruta partida si es larga
            path = e["path"]
            stdscr.addstr(4, rx, "Ruta:")
            for idx, chunk in enumerate([path[i:i+RIGHT_W] for i in range(0, len(path), max(1, RIGHT_W))]):
                if 5 + idx < H - 3:
                    stdscr.addstr(5 + idx, rx, chunk)
            stdscr.addstr(7, rx, "Enter  → abrir con Codium", curses.color_pair(3))
            stdscr.addstr(8, rx, "d      → eliminar entrada", curses.color_pair(3))
        else:
            stdscr.addstr(3, rx, "Bienvenido a config-manager")
            stdscr.addstr(5, rx, "Gestiona tus archivos de config.")
            stdscr.addstr(6, rx, "Usa ↑↓ para navegar.")
            stdscr.addstr(7, rx, "Escribe para buscar.")

    # ── Status / atajos ───────────────────────────────────────────────────────
    if status_msg:
        color = curses.color_pair(5) if status_msg.startswith("Error") else curses.color_pair(4)
        stdscr.addstr(H - 2, 2, status_msg[:W - 4], color)
    else:
        hints = "↑↓ navegar   Enter abrir   a añadir   d eliminar   ESC limpiar   q salir"
        stdscr.addstr(H - 2, 2, hints[:W - 4], curses.color_pair(3))

    stdscr.refresh()


def main(stdscr):
    entries = load_entries()
    query = ""
    selected = 0
    status_msg = ""
    mode = "browse"   # browse | search | add_name | add_path | confirm_delete
    input_buf = ""
    add_name_tmp = ""

    while True:
        filtered = [e for e in entries if query.lower() in e["name"].lower() or query.lower() in e["path"].lower()]
        selected = max(0, min(selected, len(filtered) - 1))

        draw_ui(stdscr, entries, query, selected, status_msg, mode, input_buf)
        status_msg = ""

        try:
            key = stdscr.get_wch()
        except curses.error:
            continue

        # ── Modos de input (añadir entrada) ──────────────────────────────────
        if mode in ("add_name", "add_path"):
            if key == "\x1b":  # ESC
                mode = "browse"
                input_buf = ""
                add_name_tmp = ""
            elif key in ("\n", "\r"):
                if mode == "add_name":
                    if input_buf.strip():
                        add_name_tmp = input_buf.strip()
                        input_buf = ""
                        mode = "add_path"
                    else:
                        status_msg = "El nombre no puede estar vacío"
                else:  # add_path
                    path = os.path.expanduser(input_buf.strip())
                    if path:
                        entries.append({"name": add_name_tmp, "path": path})
                        save_entries(entries)
                        status_msg = f"Guardado: {add_name_tmp}"
                    input_buf = ""
                    add_name_tmp = ""
                    mode = "browse"
            elif key in (curses.KEY_BACKSPACE, "\x7f", "\b"):
                input_buf = input_buf[:-1]
            elif isinstance(key, str) and key.isprintable():
                input_buf += key
            continue

        # ── Confirmar eliminar ────────────────────────────────────────────────
        if mode == "confirm_delete":
            if key in ("s", "S", "y", "Y"):
                if filtered and selected < len(filtered):
                    victim = filtered[selected]
                    entries = [e for e in entries if e is not victim]
                    save_entries(entries)
                    selected = max(0, selected - 1)
                    status_msg = f"Eliminado: {victim['name']}"
            mode = "browse"
            input_buf = ""
            continue

        # ── Modo browse / search ──────────────────────────────────────────────
        if key == curses.KEY_UP:
            selected = max(0, selected - 1)
        elif key == curses.KEY_DOWN:
            selected = min(len(filtered) - 1, selected + 1)
        elif key in ("\n", "\r"):
            if filtered and selected < len(filtered):
                status_msg = open_with_codium(filtered[selected]["path"])
        elif key == "a":
            mode = "add_name"
            input_buf = ""
        elif key == "d":
            if filtered:
                mode = "confirm_delete"
        elif key == "\x1b":  # ESC → limpiar búsqueda
            query = ""
            selected = 0
        elif key == "q":
            break
        elif isinstance(key, str) and key.isprintable():
            query += key
            selected = 0
        elif key in (curses.KEY_BACKSPACE, "\x7f", "\b"):
            query = query[:-1]
            selected = 0


if __name__ == "__main__":
    curses.wrapper(main)
