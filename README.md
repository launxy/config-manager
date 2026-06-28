# config-manager

Gestor de archivos de configuración con TUI en la terminal. Guarda rutas de tus configs y ábrelas directamente con Codium.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ > _                        │  config-manager                                │
│──────────────────────────  │                                                │
│   hyprland    ~/.config/h  │  Nombre: hyprland                              │
│   waybar      ~/.config/w  │  Ruta: ~/.config/hypr/hyprland.conf            │
│   sway        ~/.config/s  │                                                │
│   nvim        ~/.config/n  │  Enter  → abrir con Codium                     │
│   zsh         ~/.zshrc     │  d      → eliminar entrada                     │
│                            │                                                │
├────────────────────────────┴────────────────────────────────────────────────┤
│ ↑↓ navegar   Enter abrir   a añadir   d eliminar   ESC limpiar   q salir    │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Requisitos

- Python 3.6+
- `codium` en PATH (VSCodium)

## Instalación

```bash
git clone https://github.com/launxy/config-manager
cd config-manager
chmod +x config-manager.py
```

Opcional — instalar globalmente:

```bash
sudo cp config-manager.py /usr/local/bin/config-manager
```

## Uso

```bash
python config-manager.py
# o si está en PATH:
config-manager
```

## Controles

| Tecla | Acción |
|-------|--------|
| `↑` `↓` | Navegar por la lista |
| `Enter` | Abrir el archivo seleccionado con Codium |
| `a` | Añadir nueva entrada (nombre + ruta) |
| `d` | Eliminar entrada seleccionada |
| Escribir | Buscar en tiempo real |
| `ESC` | Limpiar búsqueda |
| `q` | Salir |

## Datos

Las entradas se guardan en:

```
~/.config/config-manager/entries.json
```

Formato:

```json
[
  { "name": "hyprland", "path": "/home/user/.config/hypr/hyprland.conf" },
  { "name": "waybar",   "path": "/home/user/.config/waybar/config" }
]
```

Puedes editar el archivo manualmente o hacer backup fácilmente.

## Sin dependencias externas

Solo stdlib de Python: `curses`, `json`, `subprocess`, `pathlib`.

