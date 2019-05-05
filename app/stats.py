"""module to compute stats"""

import math
import random
from datatypes import Lambda, VerbStats
from utils import get_progression


def _get_index(lambda_: Lambda, progression) -> Lambda:
    idx = 0
    for i, lam_val in enumerate(progression):
        if lam_val > lambda_:
            return Lambda(idx)
        idx = i
    return Lambda(idx)


def update_lambda(lambda_: Lambda, right: bool, accuracy: float) -> Lambda:
    """update the lambda value given if the word was answered correctly"""
    progression = get_progression(accuracy)
    idx = _get_index(lambda_, progression)

    return _get_max_lambda(idx, progression) if right else _get_min_lambda(idx, progression)


def _get_min_lambda(idx, progression) -> Lambda:
    return progression[idx] if idx == 0 else progression[idx - 1]


def _get_max_lambda(idx, progression) -> Lambda:
    return progression[idx] if idx == len(progression) - 1 else progression[idx + 1]


def pick(stats: VerbStats) -> bool:
    """pick the work given the stats"""
    return random.random() <= poisson_cdf(*stats)


def poisson_df(lambda_: Lambda, k: int) -> float:
    """returns the lambda mass probability"""
    return ((math.e ** -lambda_) * (lambda_ ** k)) / math.factorial(k)


def poisson_cdf(lambda_: Lambda, k: int) -> float:
    """returns the lambda cumulative distribution"""
    return sum(poisson_df(lambda_, i) for i in range(k + 1))


def logistic(accuracy: float, mean: float, discriminant: float, max_val: float) -> float:
    """returns the value of the logistic function"""
    return max_val / (1 + math.e ** (-discriminant * (accuracy - mean)))
