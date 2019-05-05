"""manages the interaction with the user"""

from PyInquirer import prompt as py_prompt
from datatypes import Name, Lang, Mode, Time, Options
from utils import read_json


def get_lang() -> Lang:
    """get the language to study"""
    question = {
        'name': 'lang',
        'type': 'list',
        'message': "what language would you like to study?",
        'choices': ['pt', 'es', 'it', 'fr']
    }

    return py_prompt(question)['lang']


def get_name() -> Name:
    """the the user name"""
    return py_prompt({
        'name': 'name',
        'type': 'input',
        'message': "what's your name?"
    })['name']


def get_mode(lang: Lang) -> Mode:
    """get the mode of the language to study"""
    modes = read_json(f"languages/{lang}/modes")

    answer = py_prompt({
        'name': 'mode',
        'type': 'list',
        'message': "what mode?",
        'choices': [mode['name'] for mode in modes.values()]
    })

    return [k for k, mode in modes.items() if answer['mode'] == mode['name']][0]


def get_time(lang: Lang, mode: Mode) -> Time:
    """get the time of the mode to study"""

    times = read_json(f"languages/{lang}/times")

    if mode not in times:
        return Time(mode)

    answer = py_prompt({
        'name': 'time',
        'type': 'list',
        'message': "what time?",
        'choices': times[mode].keys()
    })

    return times[mode][answer['time']]


def get_pre_state() -> Options:
    """get the options to initialize the app"""
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
