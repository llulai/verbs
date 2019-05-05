"""models from the application"""
import os
import csv
import json
from dataclasses import dataclass
from utils import read_json
from stats import get_lambda, logistic, select


@dataclass
class State:
    """Holds the state of the application"""
    name: str
    lang: str
    mode: str
    time: str
    has_times: bool
    has_persons: bool
    conjugations: dict
    persons_translation: dict
    persons: tuple
    min_to_review: int
    practice_list: dict  # change type
    to_learn_list: list  # change type
    total_right: int
    total_answers: int

    @property
    def total_accuracy(self):
        """calculate the accuracy"""
        return self. total_right / self.total_answers

    def get_to_review(self) -> list:
        """returns a list to be reviewed in the next session"""
        to_review = [verb for verb, stats in self.practice_list.items() if select(stats)]

        if len(to_review) < self.min_to_review:
            for _ in range(self.min_to_review - len(to_review)):
                to_review.append(self.to_learn_list.pop())

        return to_review

    def update_performance(self, reviewed_verbs: dict) -> None:
        """update the stats for the reviewed verbs"""
        for verb, right in reviewed_verbs.items():
            if verb in self.practice_list:
                lambda_, _ = self.practice_list[verb]
            else:
                lambda_, _ = (1, 0)

            self.practice_list[verb] = (get_lambda(lambda_, right, self.total_accuracy), 0)

        for verb, stats in self.practice_list.items():
            self.practice_list[verb] = (stats[0], stats[1] + 1)

        self._update_min_to_review(reviewed_verbs)

    def _update_min_to_review(self, reviewed_verbs):
        right = sum(reviewed_verbs.values())
        answers = len(reviewed_verbs.values())
        accuracy = right / answers

        self.total_right += right
        self.total_answers += answers

        x0 = min(self.total_accuracy, .925)

        multiplier = logistic(accuracy, x0, 10, 2)

        self.min_to_review = max(int(self.min_to_review * multiplier), 3)

    @classmethod
    def exists(cls, name: str, lang: str, mode: str, time: str) -> bool:
        """verifies whether a state with the given options already exists"""
        users_files = os.listdir('users')

        filename = "_".join([name, lang, mode, time]) + '.json'

        return filename in users_files

    @classmethod
    def new(cls, name: str, lang: str, mode: str, time: str):
        """creates a new state with the given options"""

        return State(name=name,
                     lang=lang,
                     mode=mode,
                     time=time,
                     has_times=get_has_times(lang, mode),
                     total_answers=1,
                     total_right=0,
                     has_persons=get_has_persons(lang, mode),
                     persons=get_persons(lang, mode),
                     persons_translation=get_pers_trans(lang),
                     min_to_review=3,
                     practice_list=dict(),
                     to_learn_list=get_verb_list(lang),
                     conjugations=get_conjugations(lang, mode, time))

    @classmethod
    def load(cls, name: str, lang: str, mode: str, time: str):
        """creates a state from a json file"""
        filename = "users/" + "_".join([name, lang, mode, time])
        json_file = read_json(filename)

        conjugations = get_conjugations(lang, mode, time)
        practicing_verbs = list(json_file['practice_list'].keys())
        to_learn_list = [verb for verb in get_verb_list(lang) if verb not in practicing_verbs]

        return State(to_learn_list=to_learn_list, conjugations=conjugations, **json_file)

    def save(self) -> None:
        """saves the current state to a json file"""
        filename = "users/" + "_".join([self.name, self.lang, self.mode, self.time]) + '.json'

        state = {
            'name': self.name,
            'lang': self.lang,
            'mode': self.mode,
            'time': self.time,
            'has_times': self.has_times,
            'has_persons': self.has_persons,
            'persons_translation': self.persons_translation,
            'persons': self.persons,
            'min_to_review': self.min_to_review,
            'practice_list': self.practice_list,
            'total_right': self.total_right,
            'total_answers': self.total_answers
        }

        with open(filename, 'w') as file:
            json.dump(state, file, indent=2)


def get_has_times(lang: str, mode: str):
    """get the times of language"""
    modes_dict = read_json(f'languages/{lang}/modes')
    mode_spec = modes_dict[mode]
    return mode_spec['has_times']


def get_has_persons(lang: str, mode: str) -> bool:
    """get if the persons the language has"""
    modes_dict = read_json(f'languages/{lang}/modes')
    mode_spec = modes_dict[mode]
    return mode_spec['persons'] != []


def get_persons(lang: str, mode: str) -> tuple:
    """get the persons of the language"""
    modes_dict = read_json(f'languages/{lang}/modes')
    mode_spec = modes_dict[mode]
    return tuple(mode_spec['persons'])


def get_conjugations(lang: str, mode: str, time: str) -> dict:
    """get the conjugations for the top 100 verbs"""
    # TODO: move conjugations to smaller functions
    all_conjugations = read_json(f'languages/{lang}/conjugations')
    modes_dict = read_json(f'languages/{lang}/modes')

    mode_spec = modes_dict[mode]

    if mode_spec['has_times']:
        return {verb: {person: conj
                       for person, conj
                       in all_conjugations[verb][mode][time].items()}
                for verb in all_conjugations}

    if mode_spec['persons']:
        return {verb: {person: conj
                       for person, conj
                       in all_conjugations[verb][mode].items()}
                for verb in all_conjugations}

    return {verb: all_conjugations[verb][mode] for verb in all_conjugations}


def get_verb_list(lang: str) -> list:
    """get the top 1000 verbs"""
    with open(f'languages/{lang}/verbs.csv', newline='') as csv_file:
        return list(reversed([word[0] for word in csv.reader(csv_file, delimiter=',')]))


def get_pers_trans(lang: str) -> dict:
    """returns a dictionary with the translation of the given persons"""
    # TODO: move to json
    trans = {
        'pt': {
            '1s': 'eu',
            '2s': 'tu',
            '3s': 'você/ele/ela',
            '1p': 'nós',
            '2p': 'vós',
            '3p': 'vocês/eles/elas'
        }
    }

    return trans[lang]
