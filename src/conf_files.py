import re

from pathlib import Path
from typing import Any, Union
from cmd import ShellCmd


def add_value_to_variable(filename: Union[str, Path],
                          variable_name: Any,
                          value: str = '',
                          quot: str = '"',
                          delim: str = ' ',
                          pretend: bool = False):
    if pretend:
        line_match = fr'[[:space:]]*{variable_name}=.*'
        value_match = fr'{quot}\([^{quot}]*\){quot}'
        sed_sub = fr'{quot}\1{delim}{value}{quot}'
        sed_script = f"sed -i '/{line_match}/ s@{value_match}@{sed_sub}@' {filename}"
        return ShellCmd(sed_script)

    variable_name_re = re.compile(fr'^\s*{variable_name}=')
    variable_value_re = re.compile(fr'{quot}([^{quot}]*){quot}')
    changed_lines = []
    with open(filename, 'r') as file:
        for line in file:
            if variable_name_re.match(line):
                changed_lines.append(variable_value_re.sub(fr'{quot}\1{delim}{value}{quot}', line))
            else:
                changed_lines.append(line)

    with open(filename, 'w') as file:
        file.writelines(changed_lines)


def remove_variable_value(filename: Union[str, Path],
                          variable_name: Any,
                          value: str = '',
                          quot: str = '"',
                          delim: str = ' ',
                          full: bool = False,
                          pretend: bool = False):
    if pretend:
        line_match = fr'[[:space:]]*{variable_name}=.*'
        sed_script = f"sed -i '/{line_match}/ s@{value}@@g' {filename}"
        if full:
            sed_script = f"sed -i '/{line_match}/d' {filename}"
        return ShellCmd(sed_script)

    variable_name_re = re.compile(fr'^\s*{variable_name}=')
    changed_lines = []
    with open(filename, 'r') as file:
        for line in file:
            if variable_name_re.match(line):
                if full:
                    continue
                changed_lines.append(line.replace(value, ''))
            else:
                changed_lines.append(line)

    with open(filename, 'w') as file:
        file.writelines(changed_lines)


def add_variable_to_file(filename: Union[str, Path],
                         variable_name: str,
                         value: str,
                         quot: str = '"',
                         pretend: bool = False):
    if pretend:
        return ShellCmd(f'''echo '{variable_name}={quot}{value}{quot}' >> {filename}''')
    with open(filename, 'a') as file:
        file.write(f'{variable_name}={quot}{value}{quot}\n')
