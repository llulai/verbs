import sys
import csv
import json
import os
from random import sample
from itertools import cycle
from termcolor import colored
from PyInquirer import prompt


def read_json(filename: str):
    """read json file"""
    with open(f'{filename}.json', 'r') as file:
        return json.loads(file.read())


def get_conjugations(lang: str) -> dict:
    """get the conjugations for the top 100 verbs"""
    return read_json(f'languages/{lang}/conjugations')


def get_verbs(lang: str) -> list:
    """get the top 1000 verbs"""
    with open(f'languages/{lang}/verbs.csv', newline='') as csv_file:
        return [word[0] for word in csv.reader(csv_file, delimiter=',')]


def get_pers_trans(lang: str) -> dict:
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


def get_seq(i: int) -> str:
    """get the id for the deck given the index of it"""
    nums = ''.join([str(i) for i in range(10)])
    out = [nums[i]]
    for delta in range(2, 5):
        out.append(nums[(i + delta) % 10])
        i += delta
    return ''.join(out)


def create_decks(verbs: list, idx: int) -> dict:
    """create default decks"""
    return {
        'current': list(verbs[:idx]),
        'progress': {get_seq(i): [] for i in range(10)},
        'retired': []
    }


def has_state(pre_state):
    return is_file(f"{pre_state['name']}_{pre_state['lang']}")


def create_state(pre_state) -> dict:
    """create default state"""
    return dict(name=pre_state['name'],
                lang=pre_state['lang'],
                mode=pre_state['mode'],
                time=pre_state['time'],
                decks=create_decks(get_verbs(pre_state['lang']), 3),
                min_current_deck_size=3,
                current_verbs_index=3)


def save_state(state: dict) -> None:
    """save the current state"""
    with open(f"users/{state['name']}_{state['lang']}_{state['time']}.json", 'w') as file:
        json.dump(state, file, indent=2)


def load_state(pre_state) -> dict:
    """load the current state"""
    return read_json(f"users/{pre_state['name']}_{pre_state['lang']}")


def ask_verb(conjugations, verb: str, mode: str, time: str, pers_trasn: dict) -> bool:
    """ask the given verb conjugations, given the mode and time"""
    persons = ('1s', '3s', '1p', '3p')

    print()
    print(colored(f"conjugate {verb}", 'yellow'))

    answers = []
    for person in persons:
        try:
            user_answer = input(f"{pers_trasn[person]}: ")
        except UnicodeDecodeError:
            user_answer = ''

        right_answer = conjugations[verb][mode][time][person]

        sys.stdout.write("\033[F")

        if user_answer == right_answer:
            print(f"{pers_trasn[person]}:", colored(f"{right_answer}", 'green'))
        else:
            print(f"{pers_trasn[person]:}:",
                  colored(f"{user_answer}", 'red'),
                  " right answer:",
                  colored(right_answer, 'green'))

        answers.append(user_answer)

    return all(answers)


def get_words_in_progress(decks: dict) -> list:
    """get words that are in progress decks"""
    return [word for words in decks['progress'].values() for word in words]


def print_summary(decks: dict) -> None:
    """prints a summary of the current state"""
    print()
    print(colored("=== SUMMARY ===", 'blue'))
    print(colored(f"words in current: {len(decks['current'])}", 'blue'))
    print(colored(f"words in progress: {len(get_words_in_progress(decks))}", 'blue'))
    print(colored(f"words learned: {len(decks['retired'])}", 'blue'))


def put_in_progress(decks: dict, session: int, word: str) -> None:
    """puts the given word in the progress deck given the session"""
    decks['progress'][get_seq(session)].append(word)


def start(state: dict):
    """start the main loop"""
    decks = state['decks']
    current_verbs_index = state['current_verbs_index']
    min_current_deck_size = state['min_current_deck_size']
    mode = state['mode']
    time = state['time']
    verbs = get_verbs(state['lang'])
    conjugations = get_conjugations(state['lang'])
    pers_trans = get_pers_trans(state['lang'])

    for session in cycle(range(10)):

        words_seen_in_current = review_current_deck(conjugations, decks, mode, time, pers_trans)

        review_progress_deck(conjugations, decks, mode, session, time, pers_trans)

        put_right_in_progress(decks, session, words_seen_in_current)

        current_verbs_index = add_verbs_to_current(current_verbs_index,
                                                   decks,
                                                   min_current_deck_size,
                                                   verbs)

        print_summary(decks)
        save_state(state)


def review_progress_deck(conjugations, decks, mode, session, time, pers_trans) -> None:
    """review the progress deck"""
    for progress_id, progress_deck in decks['progress'].items():
        if str(session) in progress_id:
            words_seen_in_progress = {}
            for verb in sample(progress_deck, len(progress_deck)):
                words_seen_in_progress[verb] = ask_verb(conjugations, verb, mode, time, pers_trans)

            if str(session) == progress_id[-1]:
                for verb, right in words_seen_in_progress.items():
                    if right:
                        progress_deck.remove(verb)
                        decks['retired'].append(verb)

            for verb, right in words_seen_in_progress.items():
                if not right:
                    progress_deck.remove(verb)
                    decks['current'].append(verb)


def review_current_deck(conjugations, decks, mode, time, pers_trans) -> dict:
    """review the current deck"""
    words_seen_in_current = {}
    current_deck = decks['current']
    for verb in sample(current_deck, len(current_deck)):
        words_seen_in_current[verb] = ask_verb(conjugations, verb, mode, time, pers_trans)
    return words_seen_in_current


def add_verbs_to_current(current_verbs_index, decks, min_current_deck_size, verbs) -> int:
    """add new verbs to current deck"""
    if len(decks['current']) < min_current_deck_size:
        n_verbs_to_add = min_current_deck_size - len(decks['current'])
        prev_idx = current_verbs_index
        current_verbs_index += n_verbs_to_add
        decks['current'].extend(verbs[prev_idx: current_verbs_index])
    return current_verbs_index


def put_right_in_progress(decks, session, words_seen_in_current) -> None:
    """put the verbs reviewed in the progress deck"""
    for verb, right in words_seen_in_current.items():
        if right:
            put_in_progress(decks, session, verb)
            decks['current'].remove(verb)


def is_file(filename: str) -> bool:
    """returns True if there is a state with the given name"""
    users = os.listdir('users')
    for user in users:
        if user.split('.')[0] == filename:
            return True
    return False


def get_lang() -> str:
    question = {
        'name': 'lang',
        'type': 'list',
        'message': "what language would you like to study?",
        'choices': ['pt', 'es', 'it', 'fr']
    }

    return prompt(question)['lang']


def get_name() -> str:
    return prompt({
        'name': 'name',
        'type': 'input',
        'message': "what's your name?"
    })['name']


def get_mode(lang: str) -> str:
    modes = {
        'indicativo': 'ind',
        'subjuntivo': 'sub'
    }
    answer = prompt({
        'name': 'mode',
        'type': 'list',
        'message': "what mode?",
        'choices': modes.keys()
    })

    return modes[answer['mode']]


def get_time(mode: str) -> str:
    times = {
        'presente': 'p',
        'pretérito perfeito': 'pp',
        'futuro do presente': 'fdpres',
        'futuro do pretérito': 'fdpret',
        'pretérito imperfeito': 'pi',
        'pretérito mais que perfeito': 'pmqp'
    }

    answer = prompt({
        'name': 'time',
        'type': 'list',
        'message': "what time?",
        'choices': times.keys()
    })

    return times[answer['time']]


def get_pre_state() -> dict:
    name = get_name()
    lang = get_lang()
    mode = get_mode(lang)
    time = get_time(mode)

    return dict(
        name=name,
        lang=lang,
        mode=mode,
        time=time
    )


def main():
    """runs the main program"""
    pre_state = get_pre_state()
    state = load_state(pre_state) if has_state(pre_state) else create_state(pre_state)

    start(state)


if __name__ == '__main__':
    main()
