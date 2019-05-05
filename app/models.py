"""models from the application"""
import os
import csv
import json
from dataclasses import dataclass
from utils import read_json
from stats import update_lambda, logistic, pick
from datatypes import Name, Lang, Mode, Time, VerbsList, VerbInf, VerbReview, Conjugations, PracticeList, Lambda


@dataclass
class State:
    """Holds the state of the application"""
    name: Name
    lang: Lang
    mode: Mode
    time: Time
    has_times: bool
    has_persons: bool
    conjugations: Conjugations
    persons_translation: dict
    persons: tuple
    min_to_review: int
    practice_list: PracticeList
    to_learn_list: VerbsList
    total_right: int
    total_answers: int

    @property
    def total_accuracy(self) -> float:
        """calculate the accuracy"""
        return self. total_right / self.total_answers

    def get_to_review(self) -> VerbsList:
        """returns a list to be reviewed in the next session"""
        to_review = [verb for verb, stats in self.practice_list.items() if pick(stats)]

        if len(to_review) < self.min_to_review:
            for _ in range(self.min_to_review - len(to_review)):
                to_review.append(self.to_learn_list.pop())

        return to_review

    def update_performance(self, reviewed_verbs: VerbReview) -> None:
        """update the stats for the reviewed verbs"""
        self._update_lambdas_of_reviewed_words(reviewed_verbs)
        self._update_last_time_reviewed()
        self._update_min_to_review(reviewed_verbs)

    def _update_lambdas_of_reviewed_words(self, reviewed_verbs: VerbReview) -> None:
        for verb, right in reviewed_verbs.items():
            self.practice_list[verb] = (update_lambda(self._get_lambda(verb), right, self.total_accuracy), 0)

    def _update_last_time_reviewed(self) -> None:
        for verb, stats in self.practice_list.items():
            self.practice_list[verb] = (stats[0], stats[1] + 1)

    def _get_lambda(self, verb: VerbInf) -> Lambda:
        return Lambda(self.practice_list[verb][0] if verb in self.practice_list else 1)

    def _update_min_to_review(self, reviewed_verbs: VerbReview):
        right = sum(reviewed_verbs.values())
        answers = len(reviewed_verbs.values())

        self._update_total_stats(right, answers)
        self.min_to_review = max(int(self.min_to_review * self._get_multiplier(right / answers)), 3)

    def _get_multiplier(self, accuracy: float):
        return logistic(accuracy, min(self.total_accuracy, .925), 10, 2)

    def _update_total_stats(self, right: int,  answers: int) -> None:
        self.total_right += right
        self.total_answers += answers

    @classmethod
    def exists(cls, name: Name, lang: Lang, mode: Mode, time: Time) -> bool:
        """verifies whether a state with the given options already exists"""
        users_files = os.listdir('users')
        filename = "_".join([name, lang, mode, time]) + '.json'

        return filename in users_files

    @classmethod
    def new(cls, name: Name, lang: Lang, mode: Mode, time: Time):
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
                     practice_list=PracticeList({}),
                     to_learn_list=get_verb_list(lang),
                     conjugations=get_conjugations(lang, mode, time))

    @classmethod
    def load(cls, name: Name, lang: Lang, mode: Mode, time: Time):
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


def get_has_times(lang: Lang, mode: Mode) -> bool:
    """get the times of language"""
    modes_dict = read_json(f'languages/{lang}/modes')
    mode_spec = modes_dict[mode]
    return mode_spec['has_times']


def get_has_persons(lang: Lang, mode: Mode) -> bool:
    """get if the persons the language has"""
    modes_dict = read_json(f'languages/{lang}/modes')
    mode_spec = modes_dict[mode]
    return mode_spec['persons'] != []


def get_persons(lang: Lang, mode: Mode) -> tuple:
    """get the persons of the language"""
    modes_dict = read_json(f'languages/{lang}/modes')
    mode_spec = modes_dict[mode]
    return tuple(mode_spec['persons'])


def get_conjugations(lang: Lang, mode: Mode, time: Time) -> Conjugations:
    """get the conjugations for the top 100 verbs"""
    conjugations = read_json(f'languages/{lang}/conjugations')
    modes_dict = read_json(f'languages/{lang}/modes')
    mode_spec = modes_dict[mode]

    if mode_spec['has_times']:
        return _get_conjugations_with_time(conjugations, mode, time)

    if mode_spec['persons']:
        return _get_conjugations_with_person(conjugations, mode)

    return _get_conjugations_simple(conjugations, mode)


def _get_conjugations_with_time(conjugations: dict, mode: Mode, time: Time) -> Conjugations:
    return {verb: {person: conj
                   for person, conj
                   in conjugations[verb][mode][time].items()}
            for verb in conjugations}


def _get_conjugations_with_person(conjugations: dict, mode: Mode) -> Conjugations:
    return {verb: {person: conj
                   for person, conj
                   in conjugations[verb][mode].items()}
            for verb in conjugations}


def _get_conjugations_simple(conjugations: dict, mode: Mode) -> Conjugations:
    return {verb: conjugations[verb][mode] for verb in conjugations}


def get_verb_list(lang: Lang) -> VerbsList:
    """get the top 1000 verbs"""
    with open(f'languages/{lang}/verbs.csv', newline='') as csv_file:
        return list(reversed([VerbInf(word[0]) for word in csv.reader(csv_file, delimiter=',')]))


def get_pers_trans(lang: Lang) -> dict:
    """returns a dictionary with the translation of the given persons"""
    return read_json(f'languages/{lang}/persons')
