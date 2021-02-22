# coding=utf-8

from __future__ import absolute_import, division, generator_stop, print_function, unicode_literals

import inspect

import chasebot

desired_functions = [
    chasebot.list_chases,
    chasebot.vote_on_chase,
    chasebot.update_chase,
    chasebot.add_chase,
    chasebot.delete_chase,
    chasebot.get_chase,
]

template = """---
title: {title}
description: 'Description for {title}'
position: {index}
category: 'Commands'
---

### Commands

<alert type="info">{commands}</alert>

### Description

{description}

### Examples

{examples}

"""


# via https://stackoverflow.com/questions/3232024/introspection-to-get-decorator-names-on-a-method
def get_decorators(function):
    """Returns list of decorators names

    Args:
        function (Callable): decorated method/function

    Return:
        List of decorators as strings

    Example:
        Given:

        @my_decorator
        @another_decorator
        def decorated_function():
            pass

        >>> get_decorators(decorated_function)
        ['@my_decorator', '@another_decorator']

    """
    source = inspect.getsource(function)
    index = source.find("def ")
    return [
        line.strip()  # .split()[0]
        for line in source[:index].strip().splitlines()
        if line.strip()[0] == "@"
    ]


docstrings = []
for index, fn in enumerate(desired_functions):
    docstring = inspect.getdoc(fn)
    description = docstring.split('e.g.')[0].strip()
    description = description.replace("!*", '<alert type="warning">').replace("*!", '</alert>')
    examples = docstring.split('e.g.')[1].split('\n')
    examples = "\n".join("```\n{}\n```".format(ex.strip()) for ex in examples)
    decorators = get_decorators(fn)
    for decorator in decorators:
        if "plugin.command" in decorator:
            commands = decorator.replace("@plugin.command(", "").replace("'", "").replace(")", "")
            commands = commands.split(",")
            commands = "  ".join("`{}`".format(command.strip()) for command in commands)
    docstrings.append(
        {
            "title": fn.__name__,
            "template": template.format(
                title=fn.__name__.replace("_", " ").title(),
                index=index + 1,
                description=description,
                examples=examples,
                commands=commands
            )
        }
    )

for index, thing in enumerate(docstrings):
    try:
        with open('./docs/content/en/cmd-{title}.md'.format(title=thing['title'].replace("_", "-")), 'w') as handle:
            handle.write(thing['template'])
    except Exception as e:
        print(e)
        pass
