import json
import numpy as np
import os
from PIL import Image
import pyautogui as ag
import six
import time
import win32gui as wg


def _load_image(image_dir, name):
    image = Image.open(os.path.join(image_dir, '{}.png'.format(name)))
    image = (np.asarray(image) > 100).astype(np.int32)
    image = image[:,:,0] * image[:,:,2]
    return image

class Solitaire(object):
    default_config = {
        'window_width': 1024,
        'window_height': 768,
        'card_width': 96,
        'card_height': 127,
        'stock_x': 110,
        'stock_y': 106,
        'waste_x': 228,
        'waste_y': 106,
        'waste_offset': 19,
        'foundation_x': 463,
        'foundation_y': 106,
        'foundation_offset': 118,
        'tableau_x': 110,
        'tableau_y': 272,
        'tableau_offset': 118,
        'tableau_down_offset': 12.4,
        'give_up_x': 62,
        'give_up_y': 725,
        'ok_x': 625,
        'ok_y': 495,
        'no_move_x': 511,
        'no_move_y': 482,
        'new_game_x': 140,
        'new_game_y': 583,
        'new_game_after_clear_x': 221,
        'new_game_after_clear_y': 583,
        'solve_x': 265,
        'solve_y': 170,
        'symbol_size': 16,
        'draw_count': 3,
    }

    def __init__(self, image_dir, output_path):
        for k, v in self.default_config.items():
            setattr(self, '_' + k, v)

        digit_images = [_load_image(image_dir, str(i + 1)) for i in six.moves.range(13)]
        self._digit_images = np.asarray(digit_images)
        suits = ['club', 'diamond', 'heart', 'spade']
        suit_images = [_load_image(image_dir, s) for s in suits]
        self._suit_images = np.asarray(suit_images)
        self._no_move_image = np.asarray([_load_image(image_dir, 'no_move_ok')])
        self._solve_image = np.asarray([_load_image(image_dir, 'solve')])

        handle = wg.FindWindow(None, "Microsoft Solitaire Collection")
        wg.SetForegroundWindow(handle)
        x, y, x2, y2 = wg.GetWindowRect(handle)
        wg.SetWindowPos(handle, 0, x, y, self._window_width, self._window_height, 0)
        self._window_x = x
        self._window_y = y
        self._output_path = output_path
        self._scores = []
        ag.PAUSE = 0

    def reset_game(self, reason=None):
        # retry to restart game when
        if reason is not None:
            card = self._detect_tableau_card(0)
            while card[0] is None:
                if reason == 'clear':
                    self._click(self._new_game_after_clear_x, self._new_game_after_clear_y)
                elif reason == 'give_up':
                    self._click(self._ok_x, self._ok_y)
                else: # 'no_move'
                    if self.has_no_move():
                        self._click(self._no_move_x, self._no_move_y)
                        time.sleep(1)
                    self._click(self._new_game_x, self._new_game_y)
                time.sleep(3)
                card = self._detect_tableau_card(0)

        self._stock = [(None, None) for i in six.moves.range(24)]
        if self._waste_is_empty():
            self._waste = []
            self.draw()
        else:
            self._waste = self._detect_waste_cards()
        self._tableau_down = []
        for i in six.moves.range(7):
            cards = [(None, None) for j in six.moves.range(i)]
            self._tableau_down.append(cards)
        self._tableau_up = []
        for i in six.moves.range(7):
            self._tableau_up.append([self._detect_tableau_card(i)])
        self._foundation = [[], [], [], []]
        self._round = 0

    def give_up(self):
        self._click(self._give_up_x, self._give_up_y)
        time.sleep(1)
        # sometimes no move dialog appears
        if self.has_no_move():
            self.accept_no_move()
            return
        self._click(self._ok_x, self._ok_y)
        self._update_result()
        time.sleep(3)
        self.reset_game('give_up')

    def draw(self):
        x = self._stock_x + self._card_width // 2
        y = self._stock_y + self._card_height // 2
        self._click(x, y)
        time.sleep(0.6)
        if self._stock[-1][0] is not None:
            for i in six.moves.range(self._draw_count):
                if self._stock == []:
                    break
                self._waste.append(self._stock.pop())
            return
        draw_cards = self._detect_waste_cards()
        if self._waste != []:
            top_card = self._waste[-1]
            for i, card in enumerate(draw_cards):
                if card == top_card:
                    draw_cards = draw_cards[i + 1:]
                    break
        for card in draw_cards:
            self._waste.append(card)
            self._stock.pop()

    def new_stock(self):
        x = self._stock_x + self._card_width // 2
        y = self._stock_y + self._card_height // 2
        self._click(x, y)
        time.sleep(0.3)
        self._round += 1
        while self._waste != []:
            self._stock.append(self._waste.pop())

    def waste_to_foundation(self, suit):
        x = self._waste_x + self._waste_offset + self._card_width // 2
        y = self._waste_y + self._card_height // 2
        self._click(x, y, button='right')
        self._foundation[suit].append(self._waste.pop())

    def waste_to_tableau(self, index):
        screen = self._screenshot()
        x1 = self._waste_x + self._waste_offset + self._card_width // 2
        y1 = self._waste_y + self._card_height // 2
        x2 = self._tableau_x + self._tableau_offset * index + self._card_width // 2
        if len(self._tableau_up[index]) == 0:
            y2 = self._tableau_y + self._card_height // 2
        else:
            y2 = self._detect_tableau_bottom(screen, index) - self._card_height // 2
        self._drag(x1, y1, x2, y2)
        self._tableau_up[index].append(self._waste.pop())

    def tableau_to_foundation(self, index, suit):
        screen = self._screenshot()
        x = self._tableau_x + self._tableau_offset * index + self._card_width // 2
        y = self._detect_tableau_bottom(screen, index) - self._card_height // 2
        self._click(x, y, button='right')
        self._foundation[suit].append(self._tableau_up[index].pop())

    def tableau_to_tableau(self, from_index, to_index, n):
        screen = self._screenshot()
        x1 = self._tableau_x + self._tableau_offset * from_index + self._card_width // 2
        bottom = self._detect_tableau_bottom(screen, from_index)
        if n == 1:
            y1 = bottom - self._card_height // 2
        else:
            top = self._tableau_y + self._tableau_down_offset * len(self._tableau_down[from_index])
            m = len(self._tableau_up[from_index])
            y1 = top + (bottom - top - self._card_height) * (2 * (m - n) + 1) / (2 * m - 2)
        x2 = self._tableau_x + self._tableau_offset * to_index + self._card_width // 2
        if len(self._tableau_up[to_index]) == 0:
            y2 = self._tableau_y + self._card_height // 2
        else:
            y2 = self._detect_tableau_bottom(screen, to_index) - self._card_height // 2
        self._drag(x1, y1, x2, y2)
        self._tableau_up[to_index].extend(self._tableau_up[from_index][-n:])
        self._tableau_up[from_index] = self._tableau_up[from_index][:-n]

    def foundation_to_tableau(self, suit, index):
        screen = self._screenshot()
        j = self._detect_foundation_suit(suit)
        x1 = self._foundation_x + self._foundation_offset * j + self._card_width // 2
        y1 = self._foundation_y + self._card_height // 2
        x2 = self._tableau_x + self._tableau_offset * index + self._card_width // 2
        if len(self._tableau_up[index]) == 0:
            y2 = self._tableau_y + self._card_height // 2
        else:
            y2 = self._detect_tableau_bottom(screen, index) - self._card_height // 2
        self._drag(x1, y1, x2, y2)
        self._tableau_up[index].append(self._foundation[suit].pop())

    def flip(self, index):
        screen = self._screenshot()
        self._tableau_down[index].pop()
        self._tableau_up[index].append(self._detect_tableau_card(index))

    def has_no_move(self):
        screen = self._screenshot()
        size = self._symbol_size
        return self._find_symbol(screen, self._no_move_image, self._no_move_x,
            self._no_move_y, size + 4, size + 4, threshold=36) >= 0

    def accept_no_move(self):
        self._click(self._no_move_x, self._no_move_y)
        time.sleep(1)
        self._click(self._new_game_x, self._new_game_y)
        self._update_result()
        time.sleep(3)
        self.reset_game('no_move')

    def can_solve(self):
        screen = self._screenshot()
        size = self._symbol_size
        return self._find_symbol(screen, self._solve_image, self._solve_x,
            self._solve_y, size + 4, size + 4, threshold=36) >= 0

    def solve(self):
        self._click(self._solve_x, self._solve_y)
        time.sleep((52 - sum([len(f) for f in self._foundation])) * 0.1)
        self.clear_game()

    def clear_game(self):
        time.sleep(5)
        self._click(self._new_game_after_clear_x, self._new_game_after_clear_y)
        time.sleep(3)
        self._click(self._new_game_after_clear_x, self._new_game_after_clear_y)
        self._update_result(clear=True)
        time.sleep(3)
        self.reset_game('clear')

    @property
    def cards(self):
        return {
            'stock': self._stock,
            'waste': self._waste,
            'tableau_down': self._tableau_down,
            'tableau_up': self._tableau_up,
            'foundation': self._foundation,
        }

    @property
    def round(self):
        return self._round

    def _update_result(self, clear=False):
        score = 0
        if clear:
            score = 52 * 5
        else:
            for f in self._foundation:
                score += len(f) * 5
        score -= 52
        self._scores.append(score)
        with open(self._output_path, 'w') as f:
            json.dump({'scores': self._scores}, f)

    def _mouse_down(self, x, y, button='left'):
        ag.moveTo(x + self._window_x, y + self._window_y)
        time.sleep(0.1)
        ag.mouseDown(button=button)

    def _mouse_up(self, button='left'):
        ag.mouseUp(button=button)

    def _click(self, x, y, button='left'):
        self._mouse_down(x, y, button=button)
        time.sleep(0.1)
        self._mouse_up(button=button)

    def _drag(self, x1, y1, x2, y2):
        self._mouse_down(x1, y1)
        time.sleep(0.1)
        ag.moveTo(x2 + self._window_x, y2 + self._window_y)
        time.sleep(0.1)
        self._mouse_up()

    def _screenshot(self):
        image = ag.screenshot()
        x = self._window_x
        x2 = x + self._window_width
        y = self._window_y
        y2 = y + self._window_height
        image = np.asarray(image)[y:y2,x:x2,:]
        image = (image > 100).astype(np.int32)
        return image[:,:,0] * image[:,:,2]

    def _waste_is_empty(self):
        return self._detect_waste_cards() == []

    def _detect_waste_cards(self):
        result = []
        y = self._waste_y
        for i in six.moves.range(3):
            x = self._waste_x + self._waste_offset * i
            x = int(round(x))
            card = self._detect_card(x, y)
            if card[0] is None:
                break
            result.append(card)
        return result

    def _detect_tableau_card(self, index):
        x = self._tableau_x + self._tableau_offset * index
        y = self._tableau_y + self._tableau_down_offset * len(self._tableau_down[index])
        x = int(round(x))
        y = int(round(y))
        return self._detect_card(x, y)

    def _detect_tableau_bottom(self, screen, index):
        x = self._tableau_x + self._tableau_offset * index + self._card_width // 2
        y = self._tableau_y + self._tableau_down_offset * len(self._tableau_down[index])
        x = int(round(x))
        y = int(round(y))
        is_black = screen[y:,x][::-1] > 0
        cumsum = np.cumsum(is_black[10:])
        bottom = np.sum(cumsum == 0) + 10
        return self._window_height - bottom

    def _detect_foundation_suit(self, suit):
        y = self._foundation_y
        for i in six.moves.range(4):
            x = self._foundation_x + self._foundation_offset * i
            x = int(round(x))
            card = self._detect_card(x, y)
            if card[1] == suit:
                return i
        return -1

    def _detect_card(self, x, y):
        screen = self._screenshot()
        card = (None, None)
        size = self._symbol_size
        digit = self._find_symbol(screen, self._digit_images, x, y + 2, size + 4, size + 4)
        suit = self._find_symbol(screen, self._suit_images, x, y + size + 2, size + 4, size + 4)
        if digit >= 0 and suit >= 0:
            return (digit, suit)
        return (None, None)

    def _find_symbol(self, screen, symbols, x=0, y=0, w=None, h=None, threshold=32):
        _, sh, sw = symbols.shape
        height, width = screen.shape
        if w is None:
            w = width - x
        if h is None:
            h = width - h
        min_diff = threshold
        min_index = -1
        for i in six.moves.range(x, x + w - sw):
            for j in six.moves.range(y, y + w - sh):
                diffs = np.sum(np.absolute(symbols - screen[j:j + sh, i:i + sw]), axis=(1, 2))
                k = np.argmin(diffs)
                if diffs[k] < min_diff:
                    min_diff = diffs[k]
                    min_index = k
        return min_index
