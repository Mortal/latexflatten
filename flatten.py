import os
import re
import argparse
import subprocess


def resolve_input(fp):
    for line in fp:
        mo = re.match(r'\\input\{(.*)\} *(%.*)?$', line)
        if mo:
            with open(mo.group(1) + '.tex') as fp_:
                yield from resolve_input(fp_)
        else:
            yield line


def load_recursive(filename):
    with open(filename) as fp:
        yield from resolve_input(fp)


def process_ifs(iterable):
    ifstack = [True]
    flags = {'true': True, 'false': False}
    for raw_line in iterable:
        line = raw_line.strip()
        if '%' in line:
            line = line[:line.index('%')]
        handled = False
        if line.startswith(r'\newif'):
            flag = line[9:].split()[0]
            flags[flag] = False
            handled = True
        for flag in flags.keys():
            if handled:
                break
            elif line.startswith(r'\%strue' % flag):
                flags[flag] = True
            elif line.startswith(r'\%sfalse' % flag):
                flags[flag] = False
            elif line.startswith(r'\if%s' % flag):
                ifstack.append(flags[flag])
            else:
                continue
            handled = True
        if handled:
            pass
        elif line.startswith(r'\else'):
            ifstack[-1] = not ifstack[-1]
            handled = True
        elif line and line.split()[0] == r'\fi':
            ifstack.pop()
            handled = True

        if ifstack[-1]:
            if handled:
                if '%' not in raw_line:
                    yield '\n'
            else:
                yield raw_line
    if ifstack != [True]:
        raise Exception("Unmatched if: %s" % ifstack)


def process_macros(iterable):
    macros = 'fxnote BigO Sort Scan rfig rtab rsec rapp picheight'.split()
    defn = re.compile(
        r'^\\newcommand\{\\(?P<name>[^}]+)\}' +
        r'(?:\[(?P<arity>\d+)\])?' +
        r'\{(?P<body>.*)\}$')
    defs = {}
    for raw_line in iterable:
        line = raw_line.strip()
        mo = defn.match(line)
        if mo and mo.group('name') in macros:
            arity = int(mo.group('arity') or '0')
            defs[mo.group('name')] = (arity, mo.group('body'))
            continue
        for macro, (arity, body) in defs.items():
            pattern = r'\\%s%s' % (macro, arity * r'\{([^}]*)\}')
            repl = body.replace('\\', '\\\\').replace('#', '\\')
            raw_line = re.sub(pattern, repl, raw_line)
        yield raw_line


def process_assets(iterable, cb):
    for line in iterable:
        mo = re.search(r'\\includegraphics(?:\[[^]]*\])?\{([^}]*)\}', line)
        if mo:
            path = mo.group(1)
            base, ext = os.path.splitext(path)
            if ext == '':
                ext = '.pdf'
                path = base + ext
            if os.path.exists(path):
                cb(path)
                b = os.path.basename(path)
                line = line[:mo.start(1)] + b + line[mo.end(1):]
        mo = re.search(r'\\documentclass(?:\[[^]]*\])?\{([^}]*)\}', line)
        if mo:
            filename = mo.group(1) + '.cls'
            if os.path.exists(filename):
                cb(filename)
                with open(filename) as fp:
                    for _ in process_assets(fp, cb):
                        pass
        mo = re.search(r'\\bibliography\{([^}]*)\}', line)
        if mo:
            filename = mo.group(1) + '.bib'
            if os.path.exists(filename):
                cb(filename)
        yield line


def fix_blank_lines(iterable):
    par = False
    for line in iterable:
        if line == '':
            continue
        assert line.index('\n') == len(line) - 1
        if '%' in line:
            yield line
        elif line == '\n':
            if not par:
                yield line
                par = True
        else:
            mo = re.match(r'^\\(sub)*section\{.*$', line)
            if mo and not par:
                yield '\n'
            yield line
            par = False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--output-dir')
    parser.add_argument('filename')
    args = parser.parse_args()

    if not os.path.exists(args.output_dir):
        os.mkdir(args.output_dir)

    lines = load_recursive(args.filename)
    lines = process_ifs(lines)
    lines = process_macros(lines)
    assets = []
    lines = process_assets(lines, assets.append)
    lines = fix_blank_lines(lines)
    with open(os.path.join(args.output_dir, 'document.tex'), 'w') as fp:
        for line in lines:
            fp.write(line)
    if assets:
        subprocess.check_call(
            ('cp', '-at', args.output_dir) + tuple(set(assets)))


if __name__ == '__main__':
    main()
