"""utility functions"""

import json
from random import shuffle
from copy import copy


def read_json(filename: str):
    """read json file"""
    with open(f'{filename}.json', 'r') as file:
        return json.loads(file.read())


def shuffle_list(list_: list):
    """returns the given list shuffled"""
    new_list = copy(list_)
    shuffle(new_list)
    return new_list
