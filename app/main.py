"""main functions of the program"""

import sys
from collections import Counter
import colorama
from termcolor import colored
from prompt import get_pre_state
from models import State
from utils import shuffle_list
from datatypes import VerbsList, VerbInf, VerbReview

colorama.init()


def main():
    """runs the main program"""
    pre_state = get_pre_state()
    state = State.load(**pre_state) if State.exists(**pre_state) else State.new(**pre_state)

    while True:
        state.update_performance(review_verbs(state, state.get_to_review()))
        print_summary(state)
        state.save()


def review_verbs(state: State, verbs: VerbsList) -> VerbReview:
    """iterates over the given verbs"""
    return {verb: ask_verb(verb, state) for verb in shuffle_list(verbs)}


def ask_verb(verb: VerbInf, state: State) -> bool:
    """ask the given verb conjugations, given the mode and time"""

    print()
    print(colored(f"conjugate {verb}", 'yellow'))

    answers = []
    if state.has_persons:
        for person in state.persons:
            right_answer = state.conjugations[verb][person]
            message = f"{state.persons_translation[person]}:"

            answers.append(ask_conjugation(right_answer, message))

    else:
        right_answer = state.conjugations[verb]
        answers.append(ask_conjugation(right_answer))

    return all(answers)


def ask_conjugation(right_answer, message="") -> bool:
    """asks the conjugation and returns whether it was answered right or not"""
    user_answer = get_answer(message)
    print_answer(user_answer, right_answer, message)

    return is_right(user_answer, right_answer)


def get_answer(message: str = "") -> str:
    """get the answer given the message"""
    try:
        user_answer = input(f"{message} " if message else "")
    except UnicodeDecodeError:
        user_answer = ''
    return user_answer


def is_right(user_answer, right_answer):
    if ',' in right_answer:
        return any([user_answer == answer for answer in right_answer.split(',')])
    return user_answer == right_answer


def print_answer(user_answer: str, right_answer: str, message="") -> None:
    """prints the right answer"""
    sys.stdout.write("\033[F")

    if is_right(user_answer, right_answer):
        print(message,
              colored(right_answer, 'green'))
    else:
        print(message,
              colored(user_answer, 'red'),
              "- right answer:",
              colored(right_answer, 'green'))


def print_summary(state: State) -> None:
    """prints a summary of the current state"""
    print()
    print(colored("=== SUMMARY ===", 'blue'))
    counter = Counter([stats[0] for stats in state.practice_list.values()])
    print(colored(f"initial: {counter[1] + counter[2] + counter[3] + counter[5]}", 'blue'))
    print(colored(f"intermediate: {counter[8] + counter[13]}", 'blue'))
    print(colored(f"advanced: {counter[21] + counter[34]}", 'blue'))
    print(colored(f"total words: {len(state.practice_list)}", 'blue'))


if __name__ == '__main__':
    main()
