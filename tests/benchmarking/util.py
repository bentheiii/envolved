from dataclasses import dataclass
from inspect import getmodule, getsourcelines, getsource
from operator import attrgetter
from textwrap import indent
from time import process_time
from typing import List


@dataclass
class Measure:
    name: str
    hertz: float
    code: str
    highlight: bool = False

    def summary(self):
        return f'{self.name}: {self.hertz:,.0f}'

    def rst_tuple(self):
        name = self.name
        hz = format(self.hertz, ',.0f')
        if self.highlight:
            name = '**' + name + '**'
            hz = '**' + hz + '**'
        return name, hz


class Benchmark:
    def __init__(self, name: str):
        self.name = name
        self.measures: List[Measure] = []
        self.min_runs = 100
        self.max_time = 1

    def measure(self, name: str = ..., source=(...,), highlight=False):
        def ret(func):
            nonlocal name

            if name is ...:
                name = func.__name__

            code_parts = []
            mod_code, _ = getsourcelines(getmodule(func))
            for s in source:
                if s is ...:
                    source_lines = getsource(func).splitlines(keepends=True)
                    code_parts.append(''.join(source_lines[1:]))
                elif callable(s):
                    lines, lnum = getsourcelines(s)
                    lnum -= 1
                    last_line = lnum + len(lines) + 1
                    while lnum > 0:
                        if not mod_code[lnum - 1].startswith('@'):
                            break
                        lnum -= 1
                    code_parts.append(''.join(mod_code[lnum: last_line]))
                elif isinstance(s, int):
                    code_parts.append(mod_code[s])
                else:
                    start, end = s
                    code_parts.append(''.join(mod_code[start:end]))
            code = "\n\n".join(code_parts)

            start_time = process_time()
            runs = 0
            while True:
                func()
                runs += 1
                elapsed = process_time() - start_time
                if elapsed > self.max_time and runs >= self.min_runs:
                    break
            self.measures.append(Measure(name=name, hertz=runs / elapsed, code=code, highlight=highlight))
            return func

        return ret

    def summary(self):
        parts = [f'{self.name}:']
        parts.extend(('\t' + m.summary()) for m in self.measures)
        return '\n'.join(parts)

    def rst(self):
        ret = [
            self.name,
            '=' * (len(self.name) + 1)
        ]
        for m in self.measures:
            ret.extend((
                m.name,
                '-' * (len(m.name) + 1),
                '.. code-block:: python',
                ''
            ))
            ret.append(indent(m.code, '    '))

        sorted_measures = sorted(self.measures, key=attrgetter('hertz'), reverse=True)
        rows = [m.rst_tuple() for m in sorted_measures]
        name_len = max(max(len(r[0]) for r in rows), 5)
        hz_len = max(max(len(r[0]) for r in rows), 8)
        head_row = '=' * name_len + ' ' + '=' * hz_len

        ret.extend((
            'results:',
            '--------',
            head_row,
            'usage'.ljust(name_len) + ' ' + 'runs/sec'.ljust(hz_len),
            head_row,
        ))
        for n, h in rows:
            ret.append(n.ljust(name_len) + ' ' + h.ljust(hz_len))
        ret.append(head_row)
        ret.append('\n')

        return '\n'.join(ret)
