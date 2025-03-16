"""This is the main file for SpaceWarp-Remake"""
#region imports
from __future__ import annotations
from copy import deepcopy
from webbrowser import open as wb_open
from math import floor
from typing import Callable, Any
import pyxel


pyxel.init(128, 128, title="SpaceWarp")
pyxel.load("assets.pyxres")

tile_at: Callable
tile_set: Callable

Tile = tuple[int, int]

# region Constants

RIGHT, LEFT = False, True
TRANSPARENT: int = 0 # used for transparency when drawing

KEYS: set[Tile] = {(7, y) for y in range(4, 7)}

BUTTONS: set[Tile] = {(x, 6) for x in range(4, 7)}

TOP_DOORS: set[Tile] = {(x, 4) for x in range(4, 7)}
BOTTOM_DOORS: set[Tile] = {(x, 5) for x in range(4, 7)}
DOORS: set[Tile] = TOP_DOORS | BOTTOM_DOORS

EMPTY_TILE: Tile = (0, 0)
END_TILE: Tile = (0, 1)
SPAWN_TILE: set[Tile] = {(3, 4)}
FIRES: set[Tile] = {(x, y) for x in range(2) for y in range(2, 4)}
WALLS: set[Tile] = ({(x, y) for x in range(4, 8) for y in range(2)}
                    | {(x, y) for x in range(2, 6) for y in range(2, 4)})

COLLIDERS: set[Tile] = WALLS | DOORS

END_SHIP_TOP_LEFT: Tile = (0, 4)
END_SHIP: set[Tile] = {(x, y) for x in range(2) for y in range(4, 6)}

MENU: int = 0
PLAYING: int = 1
END: int = 2

def is_tile(element: Any):
    """Takes in any input, returns true if input is a tile (tuple[int, int])"""
    return (
        isinstance(element, tuple)
        and len(element) == 2 and
        isinstance(element[0], int) and
        isinstance(element[1], int)
    )

def round_half_up(n: float, decimals: int = 0):
    """Rounds a float to the nearest specified decimal digit (default is nearest unit)"""
    multiplier = 10 ** decimals
    return floor(n*multiplier + 0.5) / multiplier

class TileError(Exception):
    """Misplaced tile"""


# region Keys
class Keys:
    """Handles a set of keys of one type"""
    def __init__(self, sprite: Tile = (0, 0), state: bool = True):
        self.locations: set[Tile] = set()
        self.state: bool = state
        self.sprite: Tile = sprite

    def draw(self) -> None: # Note: this is unused
        """Draws all the keys in this class"""
        for x, y in self.locations:
            pyxel.blt(x * 8, y * 8, 0, self.sprite[0] * 8, self.sprite[1] * 8, 8, 8)

    def add(self, tile: Tile) -> None:
        """Add a location tile to the set"""
        if not is_tile(tile):
            raise TypeError("Can only add tiles to Keys")
        self.locations.add(tile)

    def __iter__(self): # also unused but i thought it would be convenient
        yield from self.locations

    def collect(self, doors: set[Doors]):
        """Run this method when a key from the set is collected"""
        self.state = False

        for door in doors:
            door.open_door(self.sprite)

    def update(self):
        """Handles the keys on the tilemap"""
        if self.state:
            for x, y in self.locations:
                tile_set(x, y, self.sprite)
        else:
            for x, y in self.locations:
                tile_set(x, y, EMPTY_TILE)

# region Buttons
class Buttons:
    """Handles a set of buttons of one type"""
    def __init__(self, sprite: Tile, state: int = 0):
        self.sprite: Tile = sprite
        self.locations: set[Tile] = set()
        self.state = state

    def add(self, tile: Tile) -> None:
        """Add a button tile to the set"""
        if not is_tile(tile):
            raise TypeError("Can only add tiles to Keys")
        self.locations.add(tile)

    def update(self):
        """Updates the state of the button"""
        self.state = max(0, self.state - 1)

    def press(self, x: int, y: int, doors: set[Doors]) -> None:
        """Run when player is on a button to set the state"""
        for button in self.locations:
            if button[0] * 8 - 4 <= x <= button[0] * 8 + 4 and button[1] * 8 == y:
                self.state = 150
            elif (
                button[0] * 8 - 5 <= x <= button[0] * 8 + 5
                and button[1] * 8 - 1 <= y <= button[1] * 8 and self.state <= 2
            ):
                self.state = 2
            elif (
                button[0] * 8 - 6 <= x <= button[0] * 8 + 6
                and button[1] * 8 - 2 < y <= button[1] * 8 and self.state <= 1
            ):
                self.state = 1

        for door in doors:
            door.button_open(self.sprite, self.state)

    def draw(self):
        """Draws every button in the set"""
        sprite_x, sprite_y = self.sprite
        sprite_x *= 8
        sprite_y *= 8

        for x, y in self.locations:
            pyxel.blt(x * 8, y * 8, 0, 0, 0, 8, 8)
            if self.state == 0:
                pyxel.blt(x * 8, y * 8, 0, sprite_x, sprite_y, 8, 8)
            elif self.state == 1:
                pyxel.blt(x * 8, y * 8 + 1, 0, sprite_x, sprite_y, 8, 7)
            elif self.state == 2:
                pyxel.blt(x * 8, y * 8 + 2, 0, sprite_x, sprite_y, 8, 6)

# region Doors
class Doors:
    """Handles a set of doors of one type"""
    def __init__(self, sprite: Tile, state: bool = True, timer: int = 0):
        self.sprite: Tile = sprite
        self.locations: set[Tile] = set()
        self.state: bool = state
        self.timer: int = timer
        self.animation_state: int = 8

    def add(self, tile: Tile) -> None:
        """Add a door tile to the set"""
        if not is_tile(tile):
            raise TypeError("Can only add tiles to Doors")
        self.locations.add(tile)

    def update(self) -> None:
        """Update the doors"""
        self.timer = max(0, self.timer - 1)

        # for animation states: 0 is open and 8 is closed

        if self.state and not self.timer:
            if self.animation_state < 8:
                self.animation_state += 1
        else:
            if self.animation_state > 0:
                self.animation_state -= 1

    def draw_animated(self, x: int, y: int):
        """Draws a door at its current state in the animation"""
        pyxel.blt(
            x * 8, y * 8,
            0,
            self.sprite[0] * 8, 40 - self.animation_state,
            8, self.animation_state
        )
        pyxel.blt(
            x * 8, y * 8 + 16 - self.animation_state,
            0,
            self.sprite[0] * 8, self.sprite[1] * 8 + 8,
            8, self.animation_state
        )

    def draw(self) -> None:
        """Draws all of the doors and sets them in the tilemap"""
        if self.state and not self.timer:
            for x, y in self.locations:
                tile_set(x, y, self.sprite)
                tile_set(x, y + 1, (self.sprite[0], self.sprite[1] + 1))
                pyxel.blt(x * 8, y * 8, 0, 16, 32, 8, 16)
                self.draw_animated(x, y)
        else:
            for x, y in self.locations:
                tile_set(x, y, EMPTY_TILE)
                tile_set(x, y + 1, EMPTY_TILE)
                self.draw_animated(x, y)

    def open_door(self, key: Tile) -> None:
        """Opens the doors if the correct key is collected"""
        if key == (7, self.sprite[0]):
            self.state = False

    def button_open(self, button: Tile, frames: int) -> None:
        """Opens the doors if the correct button is pressed"""
        if button[0] == self.sprite[0] and frames > self.timer:
            self.timer = frames

class PlayerSprite:
    """Handles the player's sprite"""
    def __init__(self, direction: bool = RIGHT):
        self.x: int = 8
        self.y: int = 0
        self.dir: bool = direction

    def update(self, moving: bool, jumping: bool) -> None:
        """Updates the sprite"""
        # just look at the assets file man, this is stupid. should I just have changed it? probably
        self.x = 8*(self.dir^moving) + 8 if jumping == 0 else 24
        self.y = 8*self.dir


    def draw(self, x: int, y: int) -> None:
        """Draws the player"""
        pyxel.blt(x, y, 0, self.x, self.y, 8, 8, TRANSPARENT)

# region Player
class Player:
    """Handles the player"""
    def __init__(self, spawn: Tile = (0, 0), *, direction: bool = RIGHT):
        self.x: int = spawn[0]
        self.y: int = spawn[1]
        self.jumping: int = 0
        self.dead: bool = False
        self.win = False
        self.sprite: PlayerSprite = PlayerSprite(direction)
        self.moving: bool = False

    def corners(self) -> tuple[Tile, Tile, Tile, Tile]:
        """Returns what tiles all four corners of the player are in"""
        return (
            tile_at(self.x // 8, self.y // 8),
            tile_at(self.x // 8, (self.y + 7) // 8),
            tile_at((self.x + 7) // 8, self.y // 8),
            tile_at((self.x + 7) // 8, (self.y + 7) // 8)
        )

    # region Player.update_position()
    def update_position(self) -> None:
        """Updates the position of the player"""
        if (tile_at(self.x // 8, self.y // 8 + 1) not in COLLIDERS
            and tile_at((self.x + 7) // 8, self.y // 8 + 1) not in COLLIDERS
        ):
            if self.jumping == 0:
                self.y += 2

        elif pyxel.btn(pyxel.KEY_UP) or pyxel.btn(pyxel.KEY_SPACE):
            self.jumping = 12

        if (
            tile_at(self.x // 8, (self.y - 1) // 8) in COLLIDERS
            or tile_at((self.x + 7) // 8, (self.y - 1) // 8) in COLLIDERS
        ):
            self.jumping = 0

        if self.jumping > 0:
            self.jumping -= 1
            self.y -= 2


        if (pyxel.btn(pyxel.KEY_RIGHT)
            and tile_at(self.x // 8 + 1, self.y // 8) not in COLLIDERS
            and tile_at(self.x // 8 + 1, (self.y + 7) // 8) not in COLLIDERS
        ):
            self.x += 1
            self.sprite.dir = RIGHT
            self.moving = not self.moving

        elif self.x > 0 and pyxel.btn(pyxel.KEY_LEFT) and (
            tile_at((self.x - 1) // 8, self.y // 8) not in COLLIDERS
            and tile_at((self.x - 1) // 8, (self.y + 7) // 8) not in COLLIDERS
        ):
            self.x -= 1
            self.sprite.dir = LEFT
            self.moving = not self.moving

        else:
            self.moving = False

    # region Player.update()
    def update(
            self,
            spawn: Tile = (0, 0),
            keys: dict[Tile, Keys] | None = None,
            buttons: dict[Tile, Buttons] | None = None,
            doors: set[Doors] | None = None
        ) -> None:
        """Updates the player"""
        if keys is None:
            keys = {}
        if buttons is None:
            buttons = {}
        if doors is None:
            doors = set()

        self.update_position()

        corners = self.corners()
        # print(corners)

        self.sprite.update(self.moving, self.jumping)


        if pyxel.btn(pyxel.KEY_R) or any((tile in FIRES for tile in corners)):
            self.dead = True
            self.x, self.y = spawn
            self.jumping = 0
            self.sprite.dir = RIGHT

        for corner in corners:
            if corner in KEYS:
                keys[corner].collect(doors)
            elif corner in BUTTONS:
                buttons[corner].press(self.x, self.y, doors)
            elif corner in END_SHIP:
                self.win = True

    def draw(self) -> None:
        """Draws the player"""
        self.sprite.draw(self.x, self.y)


# region App
class App:
    """The main app itself"""
    def __init__(self):
        self.difficulty: int = 1
        self.spawn: Tile = (0, 0)

        self.keys: list[dict[Tile, Keys]]
        self.buttons: list[dict[Tile, Buttons]]
        self.doors: list[dict[Tile, Doors]]
        self.player: Player
        self.camera: int

        self.game_state: int = MENU

        self.default_menu: list[tuple[str, Callable]] = [
            ("Start", self.start),
            ("Difficulty", self.menu_difficulty),
            ("Help", self.get_help)
        ]

        self.difficulty_menu: list[tuple[str, Callable]] = [
            ("Easy", self.change_difficulty),
            ("Normal", self.change_difficulty),
            ("Hard", self.change_difficulty),
            ("Lunatic", self.change_difficulty),
            ("Back", self.difficulty_back)
        ]

        self.selected_option: int = 0
        self.current_menu: list[tuple] = self.default_menu

        pyxel.run(self.update, self.draw)

    def save_state(self) -> None:
        """Saves the current state of the game"""
        self.saved_state = deepcopy((self.keys, self.buttons, self.doors))

    def load_state(self) -> None:
        """Loads the current state of the game"""
        self.keys, self.buttons, self.doors = deepcopy(self.saved_state)

    # region App.update()
    def update(self) -> None:
        """Updates the game"""
        if self.game_state == END:
            if pyxel.btn(pyxel.KEY_RETURN):
                self.game_state = MENU
            return

        if self.game_state == MENU:
            self.update_menu()
            return

        if pyxel.btnp(pyxel.KEY_Q):
            self.game_state = MENU

        if self.camera != (self.player.x + 4) // 128:
            self.spawn = (
                self.player.x + 4 - 8 * int(self.camera > (self.player.x + 4) // 128),
                self.player.y
            )
            self.camera = (self.player.x + 4) // 128
            self.save_state()

        self.player.update(
            self.spawn,
            self.keys[self.camera],
            self.buttons[self.camera],
            set(self.doors[self.camera].values())
        )

        if self.player.dead:
            self.load_state()
            self.player.dead = False

        for doors in self.doors[self.camera].values():
            doors.update()

        for buttons in self.buttons[self.camera].values():
            buttons.update()

        for keys in self.keys[self.camera].values():
            keys.update()

        if self.player.win:
            self.end_frame = pyxel.frame_count
            self.total_time = (self.end_frame - self.start_frame) / 30
            self.game_state = END

    def draw(self) -> None:
        """Draws the game"""
        if self.game_state == MENU:
            self.draw_menu()
            return

        pyxel.camera(self.camera * 128, 0)
        pyxel.bltm(0, 0, self.difficulty, 0, 0, self.nrooms * 128, 128)
        for doors in self.doors[self.camera].values():
            doors.draw()
        for buttons in self.buttons[self.camera].values():
            buttons.draw()

        if self.game_state == END:
            self.draw_end()
            return
        self.player.draw()

    def get_nrooms(self) -> int:
        """Gets the number of rooms of the current difficulty"""
        for i in range(1, 16):
            if tile_at(16*i, 0) == END_TILE:
                return i
        return 16

    # region Menu functions
    def start(self) -> None:
        """
        Sets all of the information needed when the game starts
        Runs when start button is pressed in the menu
        """
        global tile_at, tile_set

        self.start_frame: int = pyxel.frame_count
        self.end_frame: int

        tile_at = pyxel.tilemaps[self.difficulty].pget
        tile_set = pyxel.tilemaps[self.difficulty].pset

        self.nrooms: int = self.get_nrooms()

        # check the start of the __init__ function for the annotations
        self.keys = [{key : Keys(key) for key in KEYS} for _ in range(self.nrooms)]
        self.buttons = [
            {button : Buttons(button) for button in BUTTONS} for _ in range(self.nrooms)
        ]
        self.doors = [
            {door : Doors(door) for door in TOP_DOORS} for _ in range(self.nrooms)
        ]

        ship_locations: set[Tile] = set()
        ship_in_room: bool = False

        for y in range(16):
            for x in range(self.nrooms * 16):
                tile = tile_at(x, y)
                if tile in SPAWN_TILE:
                    self.spawn = x * 8, y * 8
                    tile = EMPTY_TILE

                elif tile in KEYS:
                    self.keys[x // 16][tile].add((x, y))
                    #  tile_set(x, y, EMPTY_TILE)

                elif tile in BUTTONS:
                    self.buttons[x // 16][tile].add((x, y))

                elif tile in TOP_DOORS:
                    if y == 16:
                        raise TileError("Top door cannot be at the bottom of the screen")
                    if tile_at(x, y + 1) in BOTTOM_DOORS:
                        self.doors[x // 16][tile].add((x, y))
                    else:
                        raise TileError(f"Missing bottom door at {(x, y + 1)}")

                elif tile in BOTTOM_DOORS:
                    if y == 0:
                        raise TileError("Bottom door cannot be at the top of the screen")
                    if tile_at(x, y - 1) not in TOP_DOORS:
                        raise TileError(f"Missing top door at {(x, y - 1)}")

                elif tile == END_SHIP_TOP_LEFT:
                    if ship_in_room:
                        raise TileError("Cannot have 2 end ships in the same room")
                    ship_in_room = True
                    ship_tiles: set[Tile] = {(x + i, y + j) for i in range(2) for j in range(2)}
                    if any(tile_at(*ship_tile) not in END_SHIP for ship_tile in ship_tiles):
                        raise TileError(f"Incomplete end ship at {x, y}")
                    for ship_tile in ship_tiles:
                        ship_locations.add(ship_tile)

                elif tile in END_SHIP and (x, y) not in ship_locations:
                    raise TileError("Incomplete end ship")

                if x % 16 == 0 and y % 16 == 0:
                    ship_in_room = False

                tile_set(x, y, tile)

        self.player = Player(self.spawn)
        self.camera = 0

        self.save_state()
        self.game_started: bool = True
        self.game_state = PLAYING

    def get_help(self) -> None:
        """Opens the help page"""
        wb_open("https://github.com/LMacrini/SpaceWarp-Remake/blob/main/README.md")

    def menu_difficulty(self) -> None:
        """Changes the menu to the difficulty selection"""
        self.current_menu = self.difficulty_menu
        self.selected_option = 0

    def difficulty_back(self) -> None:
        """Changes the menu from the difficulty selection back to the default menu"""
        self.current_menu = self.default_menu
        self.selected_option = 0

    def change_difficulty(self) -> None:
        """Changes the difficulty of the game to the selected option"""
        self.difficulty = self.selected_option + 1

    def update_menu(self) -> None:
        """Updates the menu"""
        if pyxel.btnp(pyxel.KEY_DOWN):
            self.selected_option += 1
        elif pyxel.btnp(pyxel.KEY_UP):
            self.selected_option -= 1
        self.selected_option %= len(self.current_menu)

        if pyxel.btnp(pyxel.KEY_RETURN):
            self.current_menu[self.selected_option][1]()

    def draw_menu(self) -> None:
        """Draws the menu"""
        pyxel.bltm(0, 0, 0, 0, 0, 128, 128)
        for i, option in enumerate(self.current_menu):
            color = 7
            if self.current_menu == self.difficulty_menu and i + 1 == self.difficulty:
                color = 5
            if i == self.selected_option:
                color = 0
            pyxel.text(42, 8 * (i - ((len(self.current_menu) + 1)/2)) + 72, option[0], color)

    def draw_end(self) -> None:
        """Draws the end animation and end screen"""
        if self.game_started:
            self.ship_height: int = 0
            self.ship: Tile
            for y in range(16):
                for x in range(16):
                    if tile_at(x + 16*self.camera, y) == END_SHIP_TOP_LEFT:
                        self.ship = (x + 16*self.camera, y)
                        self.clear_rectangle(x + 16*self.camera, y, 2, 2)

            self.game_started = False

        if self.ship[1] * 8 + 24 - self.ship_height > 0:
            pyxel.blt(self.ship[0] * 8, self.ship[1] * 8 - self.ship_height, 0, 0, 32, 16, 16, 0)
            pyxel.blt(
                self.ship[0] * 8 + 4, self.ship[1] * 8 + 16 - self.ship_height,
                0,
                8, 16,
                8, 8,
                0
            )
            self.ship_height += 1
        else:
            self.camera = 0
            pyxel.bltm(0, 0, 0, 0, 0, 128, 128)
            pyxel.text(48, 48, "You win!", 7)
            pyxel.text(40, 56, f"Time: {round_half_up(self.total_time)}s", 7)
            pyxel.text(42, 72, "Difficulty:", 7)
            pyxel.text(48, 80, self.difficulty_menu[self.difficulty - 1][0], 0)

    def clear_rectangle(self, x: int, y: int, w: int = 1, h: int = 1) -> None:
        """Sets a rectangle in the current tilemap to be empty"""
        for dy in range(h):
            for dx in range(w):
                tile_set(x + dx, y + dy, EMPTY_TILE)



if __name__ == "__main__":
    App()
