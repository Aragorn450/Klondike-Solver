import argparse
import six
import time
import subprocess

from solitaire import Solitaire


def parse_args():
    parser = argparse.ArgumentParser('Klondike Solver')
    parser.add_argument('--image-dir', '-i', default='image',
                        help='Image directory path')
    parser.add_argument('--output', '-o', default='result.json',
                        help='Output file path')
    parser.add_argument('--exe', '-e', default='../KlondikeSolver.exe',
                        help='Solver execution file path')
    parser.add_argument('--draw', '-d', type=int, default=3,
                        help='number of draw cards')
    parser.add_argument('--round', '-r', type=int, default=3,
                        help='Maximum number of round')
    return parser.parse_args()

def card_to_string(card):
    n, s = card
    if n is None:
        return '000'
    return '{0:02d}{1:d}'.format(n + 1, s + 1)

def make_card_string(cards):
    results = []
    for down, up in zip(cards['tableau_down'], cards['tableau_up']):
        results.append(''.join(map(card_to_string, down)))
        results.append(''.join(map(card_to_string, up)))
    results.append(''.join(map(card_to_string, cards['stock'])))
    results.append(''.join(map(card_to_string, cards['waste'])))
    for f in cards['foundation']:
        results.append(''.join(map(card_to_string, f)))
    return ','.join(results)

def main():
    args = parse_args()
    ## use parsearg
    image_dir = args.image_dir
    output_path = args.output
    exe_path = args.exe
    draw_count = args.draw
    max_round = args.round

    solitaire = Solitaire(image_dir, output_path)
    solitaire.reset_game()
    seed = 1
    moves_history = ('', '', '')
    while True:
        if solitaire.has_no_move():
            solitaire.accept_no_move()
        elif solitaire.can_solve():
            solitaire.solve()
        cards = solitaire.cards
        card_string = make_card_string(cards)
        command = [exe_path, '/DC', str(draw_count), '/R', str(max_round - solitaire.round), '/C', card_string, '/SEED', str(seed)]
        seed += 1
        print(' '.join(command))
        process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
        stdout_data, stderr_data = process.communicate()
        print(stdout_data);
        results = stdout_data.split()
        moves = results[:-1]
        moves_history = (moves_history[1], moves_history[0], moves)
        # avoid reptition
        c = moves_history[2][0]
        if moves_history[0] == moves_history[2] and (c == 'C' or c == 'D' or c == 'H' or c =='S'):
            solitaire.give_up()
            continue
        score = float(results[-1])
        if solitaire.has_no_move():
            solitaire.accept_no_move()
            continue
        for move in moves:
            foundation_num = sum(len(f) for f in solitaire.cards['foundation'])
            if score <= foundation_num:
                solitaire.give_up()
                break
            elif move.startswith('DR'):
                solitaire.draw()
                break
                for i in six.moves.range(int(move[2:])):
                    solitaire.draw()
            elif move == 'NEW':
                solitaire.new_stock()
            elif move == 'WW' or move == "NONE":
                solitaire.give_up()
                break
            elif move[0] == 'W':
                if move[1] == 'C':
                    solitaire.waste_to_foundation(0)
                elif move[1] == 'D':
                    solitaire.waste_to_foundation(1)
                elif move[1] == 'H':
                    solitaire.waste_to_foundation(2)
                elif move[1] == 'S':
                    solitaire.waste_to_foundation(3)
                else:
                    solitaire.waste_to_tableau(int(move[1]) - 1)
            elif move[0] == 'C':
                solitaire.foundation_to_tableau(0, int(move[1]) - 1)
            elif move[0] == 'D':
                solitaire.foundation_to_tableau(1, int(move[1]) - 1)
            elif move[0] == 'H':
                solitaire.foundation_to_tableau(2, int(move[1]) - 1)
            elif move[0] == 'S':
                solitaire.foundation_to_tableau(3, int(move[1]) - 1)
            elif move[0] == 'F':
                time.sleep(0.5)
                solitaire.flip(int(move[1]) - 1)
            elif move[1] == 'C':
                solitaire.tableau_to_foundation(int(move[0]) - 1, 0)
            elif move[1] == 'D':
                solitaire.tableau_to_foundation(int(move[0]) - 1, 1)
            elif move[1] == 'H':
                solitaire.tableau_to_foundation(int(move[0]) - 1, 2)
            elif move[1] == 'S':
                solitaire.tableau_to_foundation(int(move[0]) - 1, 3)
            else:
                from_index = int(move[0]) - 1
                to_index = int(move[1]) - 1
                if len(move) == 2:
                    n = 1
                else:
                    n = int(move[3:])
                solitaire.tableau_to_tableau(from_index, to_index, n)
                time.sleep(0.1 * (n - 1))
            foundation_num = sum(len(f) for f in solitaire.cards['foundation'])
            if foundation_num == 52:
                solitaire.clear_game()
            time.sleep(0.1)


if __name__ == '__main__':
    main()
