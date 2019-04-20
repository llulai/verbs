import sys
import os
import pickle
from random import sample
from itertools import cycle
import pandas as pd
from termcolor import colored

# todo: start with regular verbs
# todo: log results
# todo: extend for other times/modes


def get_conjugations():
    conjugations = {}

    for verb, verb_df in pd.read_csv('top_100_pt.csv').groupby('infinitive'):
        conjugations[verb] = {}
        for mode, mode_df in verb_df.groupby('mode'):
            conjugations[verb][mode] = {}
            for time, time_df in mode_df.groupby('time'):
                conjugations[verb][mode][time] = {}
                for pers, pers_df in time_df.groupby('pess'):
                    conjugations[verb][mode][time][pers] = pers_df.conj.values[0]

    return conjugations


def get_verbs():
    return pd.read_csv('top_1000_verbs_pt.csv').verbs.values


def get_seq(i):
    nums = ''.join([str(i) for i in range(10)])
    out = [nums[i]]
    for delta in range(2, 5):
        out.append(nums[(i + delta) % 10])
        i += delta
    return ''.join(out)


def create_decks(verbs, idx):
    return {
        'current': list(verbs[:idx]),
        'progress': {get_seq(i): [] for i in range(10)},
        'retired': []
    }


def create_state(name: str) -> dict:
    return dict(name=name,
                decks=create_decks(get_verbs(), 3),
                min_current_deck_size=3,
                current_verbs_index=3)


def save_reviewer(state: dict):
    with open(f"users/{state['name']}.pickle", 'wb') as file:
        pickle.dump(state, file, pickle.HIGHEST_PROTOCOL)


def load_reviewer(filename):
    with open(f"users/{filename}.pickle", 'rb') as file:
        return pickle.load(file)


def ask_verb(conjugations, verb, mode, time):
    persons = ('eu', 'ele/ela', 'nós', 'eles/elas')

    print()
    print(colored(f"conjugate {verb}", 'yellow'))

    answers = []
    for person in persons:
        try:
            user_answer = input(f"{person}: ")
        except UnicodeDecodeError:
            user_answer = ''

        right_answer = conjugations[verb][mode][time][person]

        sys.stdout.write("\033[F")

        if user_answer == right_answer:
            print(f"{person}:", colored(f"{right_answer}", 'green'))
        else:
            print(f"{person:}:",
                  colored(f"{user_answer}", 'red'),
                  " right answer:",
                  colored(right_answer, 'green'))

        answers.append(user_answer)

    return all(answers)


def get_words_in_progress(decks):
    return [word for words in decks['progress'].values() for word in words]


def print_summary(decks: dict):
    print()
    print(colored("=== SUMMARY ===", 'blue'))
    print(colored(f"words in current: {len(decks['current'])}", 'blue'))
    print(colored(f"words in progress: {len(get_words_in_progress(decks))}", 'blue'))
    print(colored(f"words learned: {len(decks['retired'])}", 'blue'))


def put_in_progress(decks: dict, session: int, word: str):
    decks['progress'][get_seq(session)].append(word)


def start(name: str, decks: dict, current_verbs_index=3, min_current_deck_size=3):
    mode = 'indicativo'
    time = 'presente'
    verbs = get_verbs()
    conjugations = get_conjugations()

    for session in cycle(range(10)):

        words_seen_in_current = {}

        current_deck = decks['current']

        for verb in sample(current_deck, len(current_deck)):
            words_seen_in_current[verb] = ask_verb(conjugations, verb, mode, time)

        for progress_id, progress_deck in decks['progress'].items():
            if str(session) in progress_id:
                words_seen_in_progress = {}
                for verb in sample(progress_deck, len(progress_deck)):
                    words_seen_in_progress[verb] = ask_verb(conjugations, verb, mode, time)

                if str(session) == progress_id[-1]:
                    for verb, right in words_seen_in_progress.items():
                        if right:
                            progress_deck.remove(verb)
                            decks['retired'].append(verb)

                for verb, right in words_seen_in_progress.items():
                    if not right:
                        progress_deck.remove(verb)
                        decks['current'].append(verb)

        for verb, right in words_seen_in_current.items():
            if right:
                put_in_progress(decks, session, verb)
                decks['current'].remove(verb)

        if len(decks['current']) < min_current_deck_size:
            n_verbs_to_add = min_current_deck_size - len(decks['current'])
            prev_idx = current_verbs_index
            current_verbs_index += n_verbs_to_add
            decks['current'].extend(verbs[prev_idx: current_verbs_index])

        print_summary(decks)

        state = {
            'name': name,
            'decks': decks,
            'current_verbs_index': current_verbs_index,
            'min_current_deck_size': min_current_deck_size
        }
        save_reviewer(state)


def is_file(filename: str):
    users = os.listdir('users')
    for user in users:
        if user.split('.')[0] == filename:
            return True
    return False


def main():
    name = input("what's your name? ")
    state = load_reviewer(name) if is_file(name) else create_state(name)
    start(**state)


if __name__ == '__main__':
    main()
