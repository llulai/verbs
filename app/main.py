import sys
import os
import pickle
from random import sample
from itertools import cycle
import pandas as pd
from termcolor import colored

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


def save_reviewer(obj):
    with open(f"users/{obj.name}.pickle", 'wb') as file:
        pickle.dump(obj, file, pickle.HIGHEST_PROTOCOL)


def load_reviewer(filename):
    with open(f"users/{filename}.pickle", 'rb') as file:
        return pickle.load(file)


class Reviewer:
    def __init__(self, filename):
        self.name = filename
        self._current_verbs_index = 3
        self._min_current_deck_size = 3
        self.verbs = get_verbs()
        self.conjugations = get_conjugations()
        self.decks = create_decks(self.verbs, self._current_verbs_index)

    def start(self):
        mode = 'indicativo'
        time = 'presente'
        for session in cycle(range(10)):

            words_seen_in_current = {}

            verbs = self.decks['current']

            for verb in sample(verbs, len(verbs)):
                words_seen_in_current[verb] = self._ask_verb(verb, mode, time)

            for progress_id, progress_deck in self.decks['progress'].items():
                if str(session) in progress_id:
                    words_seen_in_progress = {}
                    for verb in sample(progress_deck, len(progress_deck)):
                        words_seen_in_progress[verb] = self._ask_verb(verb, mode, time)

                    if str(session) == progress_id[-1]:
                        for verb, right in words_seen_in_progress.items():
                            if right:
                                progress_deck.remove(verb)
                                self.decks['retired'].append(verb)

                    for verb, right in words_seen_in_progress.items():
                        if not right:
                            progress_deck.remove(verb)
                            self.decks['current'].append(verb)

            for verb, right in words_seen_in_current.items():
                if right:
                    self._put_in_progress(session, verb)
                    self.decks['current'].remove(verb)

            if len(self.decks['current']) < self._min_current_deck_size:
                n_verbs_to_add = self._min_current_deck_size - len(self.decks['current'])
                prev_idx = self._current_verbs_index
                self._current_verbs_index += n_verbs_to_add
                self.decks['current'].extend(self.verbs[prev_idx: self._current_verbs_index])

            self._print_summary()
            save_reviewer(self)

    def _get_words_in_progress(self):
        return [word for words in self.decks['progress'].values() for word in words]

    def _print_summary(self):
        print()
        print(colored("=== SUMMARY ===", 'blue'))
        print(colored(f"words in current: {len(self.decks['current'])}", 'blue'))
        print(colored(f"words in progress: {len(self._get_words_in_progress())}", 'blue'))
        print(colored(f"words learned: {len(self.decks['retired'])}", 'blue'))

    def _put_in_progress(self, session, word):
        self.decks['progress'][get_seq(session)].append(word)

    def _ask_verb(self, verb, mode, time):
        persons = ('eu', 'ele/ela', 'nós', 'eles/elas')

        print()
        print(colored(f"conjugate {verb}", 'yellow'))

        answers = []
        for person in persons:
            try:
                user_answer = input(f"{person}: ")
            except UnicodeDecodeError:
                user_answer = ''

            right_answer = self.conjugations[verb][mode][time][person]

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


def is_file(filename):
    users = os.listdir('users')
    for user in users:
        if user.split('.')[0] == filename:
            return True
    return False


def main():
    name = input("what's your name? ")
    if is_file(name):
        reviewer = load_reviewer(name)
    else:
        reviewer = Reviewer(name)
    reviewer.start()


if __name__ == '__main__':
    main()
