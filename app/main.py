import sys
from collections import Counter

import colorama
from termcolor import colored
from prompt import get_pre_state
from models import State
from utils import shuffle_list


colorama.init()


def main():
    """runs the main program"""
    pre_state = get_pre_state()
    state = State.load(**pre_state) if State.exists(**pre_state) else State.new(**pre_state)

    start(state)


def start(state: State):
    """start the main loop"""
    while True:
        main_loop(state)


def main_loop(state: State) -> None:
    state.update_performance(review_verbs(state, state.get_to_review()))
    print_summary(state)
    state.save()


def review_verbs(state: State, verbs: list) -> dict:
    return {verb: ask_verb(verb, state) for verb in shuffle_list(verbs)}


def ask_verb(verb: str, state: State) -> bool:
    """ask the given verb conjugations, given the mode and time"""
    # TODO refactor
    print()
    print(colored(f"conjugate {verb}", 'yellow'))

    answers = []
    if state.has_persons:
        for person in state.persons:
            try:
                user_answer = input(f"{state.persons_translation[person]}: ")
            except UnicodeDecodeError:
                user_answer = ''

            right_answer = state.conjugations[verb][person]

            sys.stdout.write("\033[F")

            if user_answer == right_answer:
                print(f"{state.persons_translation[person]}:", colored(f"{right_answer}", 'green'))
                answers.append(True)
            else:
                print(f"{state.persons_translation[person]:}:",
                      colored(f"{user_answer}", 'red'),
                      " right answer:",
                      colored(right_answer, 'green'))

                answers.append(False)
    else:
        try:
            user_answer = input(f"")
        except UnicodeDecodeError:
            user_answer = ''

        right_answer = state.conjugations[verb]

        sys.stdout.write("\033[F")

        if user_answer == right_answer:
            print(colored(f"{right_answer}", 'green'))
            answers.append(True)
        else:
            print(colored(f"{user_answer}", 'red'),
                  " right answer:",
                  colored(right_answer, 'green'))

            answers.append(False)

    return all(answers)


def print_summary(state: State) -> None:
    """prints a summary of the current state"""
    print()
    print(colored("=== SUMMARY ===", 'blue'))
    counter = Counter([stats[0] for stats in state.practice_list.values()])
    for i in [1, 2, 3, 5, 8, 13, 21]:
        print(colored(f"{i}: {counter[i]}"))
    # update number of words learned
    # print(colored(f"words in current: {state.decks.current.len}", 'blue'))
    # print(colored(f"words in progress: {len(state.decks.get_words_in_progress())}", 'blue'))
    # print(colored(f"words learned: {len(state.decks.retired)}", 'blue'))


if __name__ == '__main__':
    main()
