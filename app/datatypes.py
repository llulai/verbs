from typing import NewType, Union, Dict, List, Tuple

Name = NewType('Name', str)
Lang = NewType('Lang', str)
Mode = NewType('Mode', str)
Time = NewType('Time', str)

OptionsValues = Union[Name, Lang, Mode, Time]
Options = Dict[str, OptionsValues]
VerbInf = NewType('VerbInf', str)
VerbsList = List[VerbInf]

VerbReview = Dict[VerbInf, bool]
Conjugations = Dict[VerbInf, Union[Dict, str]]
Lambda = NewType('Lambda', int)
VerbStats = Tuple[Lambda, int]
PracticeList = Dict[VerbInf, VerbStats]
Progression = List[Lambda]