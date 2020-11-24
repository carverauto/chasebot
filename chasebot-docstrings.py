# coding=utf-8

from __future__ import absolute_import, division, generator_stop, print_function, unicode_literals

import inspect
import json
from pathlib import Path

import chasebot

desired_functions = [
    chasebot.list_chases,
    chasebot.update_chase,
    chasebot.add_chase,
    chasebot.delete_chase,
]

docstrings = []
for fn in desired_functions:
    docstrings.append(
        {
            "title": fn.__name__,
            "description": inspect.getdoc(fn)
        }
    )
    # print(docstrings)

for thing in docstrings:
    try:
        with open(str(Path.home()) + '/dev/chasebot/docs/{title}-docstrings.md'.format(title=thing['title']), 'w') as handle:
            json.dump(thing['description'], handle)
    except Exception as e:
        print(e)
        pass
