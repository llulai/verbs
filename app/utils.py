"""utility functions"""

import json
from random import shuffle
from copy import copy
from datatypes import Lambda, Progression


def read_json(filename: str):
    """read json file"""
    with open(f'{filename}.json', 'r') as file:
        return json.loads(file.read())


def shuffle_list(list_: list):
    """returns the given list shuffled"""
    new_list = copy(list_)
    shuffle(new_list)
    return new_list


def get_progression(accuracy: float) -> Progression:
    if accuracy < .75:
        return [Lambda(1),
                Lambda(2),
                Lambda(3),
                Lambda(5),
                Lambda(8),
                Lambda(13),
                Lambda(21),
                Lambda(34)]
    else:
        return [Lambda(1),
                Lambda(3),
                Lambda(8),
                Lambda(21),
                Lambda(34)]
