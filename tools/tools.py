from random import choice

from core.state import STATE


def _select_from_state(source_key, selected_key):
    selected = choice(STATE[source_key])
    STATE[selected_key] = selected
    return selected


def SelectName():
    return _select_from_state("Fantasy Name", "Selected Name")


def SelectSetting():
    return _select_from_state("Settings", "Selected Setting")


def SelectPlot():
    return _select_from_state("Plot", "Selected Plot")
