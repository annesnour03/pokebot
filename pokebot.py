import sys
import pyautogui
from time import sleep

from global_hotkeys import *
from enum import Enum

# Gui
from gui import GUI_Pokebot
from PyQt5 import QtWidgets


class Manager():
    confidence = 0.9
    class GameHotkeys(Enum):
        # Button layout
        FIGHT = 1
        BAG = 2
        POKEMON = 3
        RUN = 4

        # Moves
        FIRST_MOVE = 1
        SECOND_MOVE = 2
        THIRD_MOVE = 3
        FOURTH_MOVE = 4

    run_app = True
    images = {
        "fight_button": "assets/button_fight.png",
        "trade_title": "assets/trade_request_title.png",
        "battle_title": "assets/battle_request_title.png",
        "decline_button": "assets/decline_button.png",
        "poke_ball": "assets/pokemon_present.png",
        "elite": "assets/elite.png",
        "shiny": {
            "shiny_plain": "assets/shiny.png",
            "shiny_cave": "assets/shiny2.png",
        },
    }

    def __init__(self, *args, **kwargs) -> None:
        self.ui = kwargs["ui"]
        self.bindings = [
            [["pause"], None, self.handle_toggle],
        ]

        # Register all of our keybindingsa
        register_hotkeys(self.bindings)
        # Finally, start listening for keypresses
        start_checking_hotkeys()

    def handle_toggle(self):
        raise NotImplementedError()

    def clear_keys(self):
        clear_hotkeys()

    def set_idle(self):
        self.ui.radioButton_2.setChecked(True)
        self.run_app = False
    # Fighting commands

    @property
    def auto_fight_is_checked(self) -> bool:
        return self.ui.radioButton_4.isChecked()

    @property
    def idle_is_checked(self) -> bool:
        return self.ui.radioButton_2.isChecked()

    # Avoidance commands
    @property
    def elite_run_is_checked(self) -> bool:
        return self.ui.checkBox.isChecked()

    @property
    def shiny_stop_is_checked(self) -> bool:
        return self.ui.checkBox_2.isChecked()

    @property
    def poke_stop_is_checked(self) -> bool:
        return self.ui.checkBox_3.isChecked()

    # Anti-ban
    @property
    def reject_trade_is_checked(self) -> bool:
        return self.ui.checkBox_7.isChecked()

    @property
    def reject_battle_is_checked(self) -> bool:
        return self.ui.checkBox_8.isChecked()

    # Battle helpers
    @property
    def select_best_move_is_checked(self) -> bool:
        return self.ui.checkBox_10.isChecked()


class Movement(Manager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def handle_toggle(self):
        self.run_app = not self.run_app
        self.clear_keys()
        self.bindings = [
            [["pause"], None, self.handle_toggle],
        ]

        # Register all of our keybindings
        register_hotkeys(self.bindings)
        # Finally, start listening for keypresses
        start_checking_hotkeys()
        if self.run_app:
            self.afk()
        else:
            self.ui.radioButton_2.setChecked(True)

    def attack(self, move):
        pyautogui.press(f'{self.GameHotkeys.FIGHT.value}')
        pyautogui.press(f'{move.value}')

    def run_away(self):
        pyautogui.press(f'{self.GameHotkeys.RUN.value}')

    def handle_trade_request(self):
        if not self.reject_trade_is_checked:
            return False

        trade_title_coords = pyautogui.locateOnScreen(
            self.images["trade_title"], confidence=self.confidence)
        decline_button_coords = pyautogui.locateOnScreen(
            self.images["decline_button"], confidence=self.confidence)

        # There never was a trade request.
        if not trade_title_coords or not decline_button_coords:
            return False
        x, y, *_ = decline_button_coords
        pyautogui.click(x, y)
        return True

    def handle_battle_request(self):
        if not self.reject_battle_is_checked:
            return False

        battle_title_coords = pyautogui.locateOnScreen(
            self.images["battle_title"], confidence=self.confidence)
        decline_button_coords = pyautogui.locateOnScreen(
            self.images["decline_button"], confidence=self.confidence)

        # There never was a trade request.
        if not battle_title_coords or not decline_button_coords:
            return False
        x, y, *_ = decline_button_coords
        pyautogui.click(x, y)
        return True

    def in_battle(self, need_bool=True):
        """Returns `True` if player currently is in battle."""
        in_battle = pyautogui.locateOnScreen(
            self.images["fight_button"])
        if need_bool:
            return in_battle != None
        return in_battle

    def is_new_pokemon(self):
        """Returns `True` if this is a new pokemon"""
        if not self.poke_stop_is_checked:
            return False

        poke_ball_coords = pyautogui.locateOnScreen(
            self.images["poke_ball"], confidence=self.confidence)

        return poke_ball_coords == None

    def is_elite_pokemon(self):
        """Returns `True` if a elite pokemon is found on screen."""
        if not self.elite_run_is_checked:
            return False
        elite_coords = pyautogui.locateOnScreen(
            self.images["elite"], confidence=self.confidence)

        return elite_coords != None

    def is_shiny_pokemon(self):
        if not self.shiny_stop_is_checked:
            return False
        # We check the cave v
        for path in self.images["shiny"].values():
            shiny_coords = pyautogui.locateOnScreen(
                path, confidence=self.confidence)
            if shiny_coords != None:
                return True
        return False

    def afk(self,):
        iterations = 1
        while self.run_app and self.auto_fight_is_checked:
            pyautogui.keyDown('a')
            sleep(0.30)
            pyautogui.keyUp('a')

            pyautogui.keyDown('d')
            sleep(0.30)
            pyautogui.keyUp('d')

            if iterations % 50 == 0:
                self.handle_trade_request()
                self.handle_battle_request()
                iterations = 1

            if self.in_battle():
                # We encoutered a pokemon that we do not have yet.
                if self.is_new_pokemon():
                    self.set_idle()
                    return
                elif self.is_elite_pokemon():
                    self.run_away()
                    return
                elif self.is_shiny_pokemon():
                    self.set_idle()
                    return
                sleep(0.1)
                self.attack(self.GameHotkeys.SECOND_MOVE)
                sleep(2)
            iterations += 1
        return


def main(*args, **kwargs):
    move = kwargs["move"]
    while True:
        move.afk()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    Pokebot = QtWidgets.QMainWindow()

    ui = GUI_Pokebot(main)
    ui.setupUi(Pokebot)
    exe = Movement(ui=ui)
    Pokebot.show()
    ui.start_worker(func=main, move=exe)
    sys.exit(app.exec_())
