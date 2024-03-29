#!/usr/bin/env python3

import os
import sys

if len(sys.argv) < 3:
    sys.exit(1)

protofile = sys.argv[1]
pythonfile = sys.argv[2]

from common import *

if not read_protocol_file(protofile):
    sys.exit(2)

def args_to_type_list(args):
    for arg in args.split():
        if arg == '...':
            yield ''
        if arg in ('%d', '%i', '%u', '%x', '%ld', '%li', '%lu', '%lx'):
            yield 'int'
        if arg in ('%f', '%g'):
            yield 'float'
        if arg in ('%c', '%s'):
            yield 'str'

def write_command_key(fh, cmdlist):
    for cmd in cmdlist:
        name, defn = cmd.split(None,1)
        defkey = defn.split(None,1)[0].replace('"','')
        yield '{} = \'{}\'\n'.format(name, defkey)

def write_command_values(fh, model, cmdlist):
    for cmd in cmdlist:
        name, defn = cmd.split(None,1)
        try:
            defkey, defargs = tuple(s.replace('"','',1) for s in defn.split(None,1))
        except ValueError:
            defkey = defn.replace('"','')
            defargs = ''
        yield '\t\t\'{}\': [{}],\n'.format(defkey, ','.join(args_to_type_list(defargs)))

content = ''
with open(pythonfile, 'w') as fh:
    content += '#!/usr/bin/env python3\n'
    content += '# pylint: disable=bad-whitespace\n'
    content += '# pylint: disable=too-many-return-statements\n\n'
    content += 'CMD_ARGS = {\n'
    for model in ('ALL',)+validmodels:
        content += '\t\'{}\': {{\n'.format(model)
        content += ''.join(write_command_values(fh, model, cmds[model]))
        content += '\t},\n'
    content += '}\n\n'
    for model in ('ALL',)+validmodels:
        content += ''.join(write_command_key(fh, cmds[model]))
    content += '\n'
    for bankfunc in bankfuncs:
        bankfnkey, bankfnvalue = tuple(s.strip() for s in bankfunc.split(None,1))
        content += '{} = {}\n'.format(bankfnkey, bankfnvalue)
    flags.pop('ALL')
    for flagcategory, flagvalues in flags.items():
        content += '\n'
        for flagname, flagvalue in flagvalues:
            content += 'FLAG_{}_{} = {}\n'.format(flagcategory, flagname, flagvalue)
    content += '\n'
    for menu in menus:
        content += '{} = {}\n'.format(*tuple(s.strip() for s in menu.split(None,1)))

with open(pythonfile, 'w') as fh:
    eqlength = 0
    for line in content.split('\n'):
        if not line:
            eqlength = 0
            fh.write('\n')

        elif ' = ' in line and ' = {' not in line:
            if eqlength == 0:
                start = content.find(line)
                end = content.find('\nMENU_' if line.startswith('FLAG_') else '\n\n', start)
                eqlength = max(tuple(len(s.split(' = ',1)[0]) for s in content[start:end].split('\n')))

            key, value = line.split(' = ',1)
            padding = " "*(eqlength-len(key))
            fh.write('{}{} = {}\n'.format(key, padding, value))

        else:
            fh.write(line.replace('\t','    ')+'\n')

    fh.write('def cmd_to_str(cmd):\n')
    fh.write('    if not isinstance(cmd, str):\n')
    fh.write('        raise ValueError\n')
    for model in ('ALL',)+validmodels:
        write_command_key(fh, cmds[model])
        for cmd in cmds[model]:
            macro, key = cmd.split(None,1)
            macro = macro.strip()
            key = key.split(None,1)[0].replace('"','')
            fh.write('    if cmd == "{}":\n'.format(key))
            fh.write('        return "{}"\n'.format(macro))
    fh.write('    return "unknown"\n\n')

    fh.write('def menu_item_id_to_str(idx):\n')
    fh.write('    if not isinstance(idx, int):\n')
    fh.write('        raise ValueError\n')
    for menu in menus:
        menu_macro, menu_id = menu.split(None,1)
        fh.write('    if idx == {}:\n'.format(menu_id))
        fh.write('        return "{}"\n'.format(menu_macro))
    fh.write('    return "unknown"\n')
