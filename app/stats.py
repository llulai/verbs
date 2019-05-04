import math
import random


def get_lambda(lambda_: int, right: bool) -> int:
    progression = [1, 2, 3, 5, 8, 13, 21]
    idx = progression.index(lambda_)

    if right:
        if idx == len(progression) - 1:
            return lambda_
        return progression[idx + 1]
    if not right:
        if idx == 0:
            return progression[idx]
        return progression[idx - 1]


def select(stats: tuple) -> bool:
    lambda_, k = stats

    return random.random() <= poisson_cdf(lambda_, k)


def poisson_df(lambda_: int, k: int) -> float:
    return ((math.e ** -lambda_) * (lambda_ ** k)) / math.factorial(k)


def poisson_cdf(lambda_: int, k: int) -> float:
    return sum(poisson_df(lambda_, i) for i in range(k + 1))


def logistic(x, x0, k, l):
    return l / (1 + math.e ** (-k * (x - x0)))
