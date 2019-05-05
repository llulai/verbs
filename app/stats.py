import math
import random
from datatypes import Lambda, VerbStats
from utils import get_progression


def _get_index(lambda_: Lambda, progression) -> Lambda:
    idx = 0
    for i, l in enumerate(progression):
        if l > lambda_:
            return Lambda(idx)
        idx = i
    return Lambda(idx)


def update_lambda(lambda_: Lambda, right: bool, accuracy: float) -> Lambda:
    progression = get_progression(accuracy)
    idx = _get_index(lambda_, progression)

    return _get_max_lambda(idx, progression) if right else _get_min_lambda(idx, progression)


def _get_min_lambda(idx, progression) -> Lambda:
    return progression[idx] if idx == 0 else progression[idx - 1]


def _get_max_lambda(idx, progression) -> Lambda:
    return progression[idx] if idx == len(progression) - 1 else progression[idx + 1]


def pick(stats: VerbStats) -> bool:
    return random.random() <= poisson_cdf(*stats)


def poisson_df(lambda_: Lambda, k: int) -> float:
    return ((math.e ** -lambda_) * (lambda_ ** k)) / math.factorial(k)


def poisson_cdf(lambda_: Lambda, k: int) -> float:
    return sum(poisson_df(lambda_, i) for i in range(k + 1))


def logistic(x, x0, k, l):
    return l / (1 + math.e ** (-k * (x - x0)))
