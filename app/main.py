import sys
import csv
import json
import os
import dataclasses
from dataclasses import dataclass
from random import sample
from termcolor import colored
from PyInquirer import prompt
import colorama

colorama.init()


class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)


@dataclass
class CurrentDeck:
    min_size: int
    deck: list

    @property
    def len(self) -> int:
        return len(self.deck)

    @property
    def random(self) -> list:
        return sample(self.deck, self.len)


@dataclass
class Decks:
    current: CurrentDeck
    progress: dict
    retired: list

    def get_words_in_progress(self) -> list:
        return [word for words in self.progress.values() for word in words]


@dataclass
class State:
    name: str
    lang: str
    mode: str
    time: str
    decks: Decks
    current_verbs_index: int
    current_session: int

    def next_session(self):
        self.current_session = (self.current_session + 1) % 10


@dataclass
class Conjugations:
    lang: str
    has_time: bool
    has_persons: bool
    conjugations: dict
    persons: tuple

@dataclass
class Verbs:
    verbs: list
    mode: str
    time: str
    conjugations: Conjugations
    pers_trans: dict


def read_json(filename: str):
    """read json file"""
    with open(f'{filename}.json', 'r') as file:
        return json.loads(file.read())


def get_conjugations(lang: str, mode: str, time: str) -> Conjugations:
    """get the conjugations for the top 100 verbs"""
    # todo: only the given mode/time
    all_conjugations = read_json(f'languages/{lang}/conjugations')

    if time in {'af', 'n'}:
        persons = ('3s', '1p', '3p')
    else:
        persons = ('1s', '3s', '1p', '3p')

    if mode != time:
        return Conjugations(lang=lang,
                            has_time=True,
                            has_persons=True,
                            conjugations={verb:{person:conj
                                                for person, conj in all_conjugations[verb][mode][time].items()}
                                          for verb in all_conjugations },
                            persons=persons)
    if mode in {'ger', 'par'}:
        return Conjugations(lang=lang,
                            has_time=False,
                            has_persons=False,
                            conjugations={verb: all_conjugations[verb][mode] for verb in all_conjugations},
                            persons=tuple())
    if mode == 'ip':
        return Conjugations(lang=lang,
                            has_time=False,
                            has_persons=True,
                            conjugations={verb: {person: conj for person, conj in all_conjugations[verb][mode].items()}
                                          for verb in all_conjugations},
                            persons=persons)
    else:
        raise AttributeError



def get_verb_list(lang: str) -> list:
    """get the top 1000 verbs"""
    with open(f'languages/{lang}/verbs.csv', newline='') as csv_file:
        return [word[0] for word in csv.reader(csv_file, delimiter=',')]


def get_verbs(state: State) -> Verbs:
    return Verbs(verbs=get_verb_list(state.lang),
                 conjugations=get_conjugations(state.lang, state.mode, state.time),
                 pers_trans=get_pers_trans(state.lang),
                 mode=state.mode,
                 time=state.time)


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


def create_decks(verbs: list, idx: int) -> Decks:
    """create default decks"""
    return Decks(current=CurrentDeck(deck=verbs[:idx], min_size=3),
                 progress={get_seq(i): [] for i in range(10)},
                 retired=[])


def has_state(pre_state):
    return is_file(f"{pre_state['name']}_{pre_state['lang']}")


def create_state(pre_state, idx=3) -> State:
    """create default state"""
    return State(name=pre_state['name'],
                 lang=pre_state['lang'],
                 mode=pre_state['mode'],
                 time=pre_state['time'],
                 decks=create_decks(get_verb_list(pre_state['lang']), idx),
                 current_verbs_index=idx,
                 current_session=0)


def save_state(state: State) -> None:
    """save the current state"""
    with open(f"users/{state.name}_{state.lang}_{state.mode}_{state.time}.json", 'w') as file:
        json.dump(state, file, indent=2, cls=EnhancedJSONEncoder)


def load_state(pre_state) -> dict:
    """load the current state"""
    return read_json(f"users/{pre_state['name']}_{pre_state['lang']}")


def ask_verb(verb: str, verbs: Verbs) -> bool:
    """ask the given verb conjugations, given the mode and time"""
    print()
    print(colored(f"conjugate {verb}", 'yellow'))

    answers = []
    if verbs.conjugations.has_persons:
        for person in verbs.conjugations.persons:
            try:
                user_answer = input(f"{verbs.pers_trans[person]}: ")
            except UnicodeDecodeError:
                user_answer = ''

            right_answer = verbs.conjugations.conjugations[verb][person]

            sys.stdout.write("\033[F")

            if user_answer == right_answer:
                print(f"{verbs.pers_trans[person]}:", colored(f"{right_answer}", 'green'))
            else:
                print(f"{verbs.pers_trans[person]:}:",
                      colored(f"{user_answer}", 'red'),
                      " right answer:",
                      colored(right_answer, 'green'))

            answers.append(user_answer)
    else:
        try:
            user_answer = input(f"")
        except UnicodeDecodeError:
            user_answer = ''


        right_answer = verbs.conjugations.conjugations[verb]

        sys.stdout.write("\033[F")

        if user_answer == right_answer:
            print(colored(f"{right_answer}", 'green'))
        else:
            print(colored(f"{user_answer}", 'red'),
                  " right answer:",
                  colored(right_answer, 'green'))

        answers.append(user_answer)

    return all(answers)


def print_summary(state: State) -> None:
    """prints a summary of the current state"""
    print()
    print(colored("=== SUMMARY ===", 'blue'))
    print(colored(f"words in current: {state.decks.current.len}", 'blue'))
    print(colored(f"words in progress: {state.decks.get_words_in_progress()}", 'blue'))
    print(colored(f"words learned: {len(state.decks.retired)}", 'blue'))


def put_in_progress(word: str, state: State) -> None:
    """puts the given word in the progress deck given the session"""
    state.decks.progress[get_seq(state.current_session)].append(word)

def main_loop(state: State, verbs: Verbs) -> None:
    words_seen_in_current = review_current_deck(state, verbs)
    review_progress_deck(state, verbs)
    put_right_in_progress(words_seen_in_current, state)
    add_verbs_to_current(state, verbs)

    print_summary(state)
    state.next_session()
    save_state(state)


def start(state: State):
    """start the main loop"""
    verbs = get_verbs(state)

    while True:
        main_loop(state, verbs)




def review_progress_deck(state: State, verbs: Verbs) -> None:
    """review the progress deck"""
    for progress_id, progress_deck in state.decks.progress.items():
        if str(state.current_session) in progress_id:
            words_seen_in_progress = {}
            for verb in sample(progress_deck, len(progress_deck)):
                words_seen_in_progress[verb] = ask_verb(verb, verbs)

            if str(state.current_session) == progress_id[-1]:
                for verb, right in words_seen_in_progress.items():
                    if right:
                        progress_deck.remove(verb)
                        state.decks.retired.append(verb)

            for verb, right in words_seen_in_progress.items():
                if not right:
                    progress_deck.remove(verb)
                    state.decks.current.deck.append(verb)


def review_current_deck(state: State, verbs: Verbs) -> dict:
    """review the current deck"""
    return {verb: ask_verb(verb, verbs) for verb in state.decks.current.random}


def add_verbs_to_current(state: State, verbs: Verbs) -> None:
    """add new verbs to current deck"""
    if len(state.decks.current.deck) < state.decks.current.min_size:
        n_verbs_to_add = state.decks.current.min_size - len(state.decks.current.deck)
        prev_idx = state.current_verbs_index
        state.current_verbs_index += n_verbs_to_add
        state.decks.current.deck.extend(verbs.verbs[prev_idx: state.current_verbs_index])


def put_right_in_progress(words_seen_in_current: dict, state: State) -> None:
    """put the verbs reviewed in the progress deck"""
    for verb, right in words_seen_in_current.items():
        if right:
            put_in_progress(verb, state)
            state.decks.current.deck.remove(verb)


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
    modes = read_json(f"languages/{lang}/modes")

    answer = prompt({
        'name': 'mode',
        'type': 'list',
        'message': "what mode?",
        'choices': modes[lang].keys()
    })

    return modes[lang][answer['mode']]


def get_time(lang: str, mode: str) -> str:

    if lang == 'pt' and mode in {'ger', 'par', 'ip'}:
        return mode

    times = {
        'pt': {
            'ind': {
                'presente': 'p',
                'pretérito perfeito': 'pp',
                'futuro do presente': 'fdpres',
                'futuro do pretérito': 'fdpret',
                'pretérito imperfeito': 'pi',
                'pretérito mais que perfeito': 'pmqp'
            },
            'sub': {
                'presente': 'p',
                'pretérito imperfeito': 'pi',
                'futuro': 'f'
            },
            'imp': {
                'afirmativo': 'af',
                'negativo': 'neg'
            }
        }
    }



    answer = prompt({
        'name': 'time',
        'type': 'list',
        'message': "what time?",
        'choices': times[lang][mode].keys()
    })

    return times[lang][mode][answer['time']]


def get_pre_state() -> dict:
    name = get_name()
    lang = get_lang()
    mode = get_mode(lang)
    time = get_time(lang, mode)

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
