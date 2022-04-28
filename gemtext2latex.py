#!/usr/bin/env python3

# gemtext2latex, A Gemini to LaTeX text converter, by Martin Keegan
#
# To the extent (if any) permissible by law, Copyright (C) 2022  Martin Keegan
#
# This programme is free software; you may redistribute and/or modify it under
# the terms of the Apache Software Licence v2.0.

import logging
import argparse
import sys
import re

DOC_CLASS='mk-plain'

DOC_TOP = '''
\\begin{document}
'''

DOC_TAIL = '''
\\end{document}
'''

def latex_quote(s):
    return re.sub(r'([%$}{_#&])',
                  (lambda x: "\\" + x.groups(0)[0]),
                  s)

class Section:
    def __init__(self, line):
        self.line = line

    def __repr__(self):
        s = latex_quote(self.line)
        c = __class__.__name__
        return f"{c}: {s}\n"


class Heading(Section):
    def __init__(self, line):
        level = len(line.split(" ", 2)[0])
        self.line = line[level:].lstrip(" ")
        self.level = level

    def __repr__(self):
        level = "sub" * (self.level - 1)
        cmd = f"\x5c{level}section*"
        s = latex_quote(self.line)
        return f"{cmd}\x7b{s}\x7d\n"


class Preformatted(Section):
    def __init__(self, _line):
        self.line = []

    def __repr__(self):
        top = "\\begin{verbatim}\n"
        tail = "\n\\end{verbatim}\n"
        lines = "\n".join(self.line)
        return f"{top}{lines}{tail}"

    def append(self, line):
        self.line.append(line)


class Link(Section):
    def __init__(self, line):
        relevant = line[3:]
        parts = relevant.split(" ", 1)
        self.caption = None
        if len(parts) > 1:
            self.caption = parts[1]
        self.referent = parts[0]

    def __repr__(self):
        if self.caption is not None:
            return "\\href{%s}{%s}" % (self.referent, self.caption)
        return "\\href{%s}" % self.referent


# yes, I am well aware this should be factored together with
# the List class below.  I don't care
class Links(Section):
    def __init__(self, i):
        self.items = [i]

    def append(self, i):
        self.items.append(i)

    def __repr__(self):
        top = "\\begin{itemize}\n"
        tail = "\n\\end{itemize}\n"
        items = "\n".join([ "\\item " + i.__repr__() for i in self.items ])

        return f"{top}{items}{tail}"


class Item(Section):
    def __init__(self, line):
        self.line = line[2:]
    
    def __repr__(self):
        return latex_quote(self.line)


class Paragraph(Section):
    def __repr__(self):
        s = latex_quote(self.line)
        return f"{s}\n"


class List(Section):
    def __init__(self, i):
        self.items = [i]

    def append(self, i):
        self.items.append(i)

    def __repr__(self):
        top = "\\begin{itemize}\n"
        tail = "\n\\end{itemize}\n"
        items = "\n".join([ "\\item " + i.__repr__() for i in self.items ])

        return f"{top}{items}{tail}"


def sections(input_stream):
    """Get the various sections of the text:
       links, paragraphs, headings, preformatted.
    """

    def fragments():
        preformatted = None

        for line in input_stream.readlines():
            line = line.rstrip("\r\n")

            if preformatted is not None:
                if line.startswith("```"):
                    yield preformatted
                    preformatted = None
                else:
                    preformatted.append(line)
                continue

            if line.startswith("```"):
                preformatted = Preformatted(line)
                continue

            if line == "":
                continue

            elif re.match(r"^#{1,3} ", line):
                yield Heading(line)

            elif line.startswith("=> "):
                yield Link(line)

            elif line.startswith("* "):
                yield Item(line)

            else:
                yield Paragraph(line)

    def group_fragments(source, member_class, group_class):
        current = None
        for frag in source():
            if current is None:
                # i.e., there is no list, but we might be about to encounter one
                if isinstance(frag, member_class):
                    current = group_class(frag)
                else:
                    yield frag
            else:
                # i.e., there is a list, but it might be about to come to an end
                if isinstance(frag, member_class):
                    current.append(frag)
                else:
                    yield current
                    current = None
                    yield frag

        if current is not None:
            yield current

    # could be more elegant, but at least it deduplicates somewhat what had
    # gone before
    def fragments_with_item_lists():
        for frag in group_fragments(fragments, Item, List):
            yield frag

    def fragments_with_all_lists():
        for frag in group_fragments(fragments_with_item_lists, Link, Links):
            yield frag

    for frag in fragments_with_all_lists():
        yield frag


def main(args, input_stream):
    print("\\documentclass{%s}" % args.docclass)
    print(f"{args.top}")
    for sect in sections(input_stream):
        print(f"{sect}")
    print(f"{args.tail}")

def run():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--debug',
        action='store_true',
        required=False,
        help='set logging level to INFO (etc)'
    )
    parser.add_argument(
        '--top',
        default=DOC_TOP,
        help=("set the preamble before the content. " +
              "Must include the \\begin{document} line.")
    )
    parser.add_argument(
        '--tail',
        default=DOC_TAIL,
        help=("set the endmatter after the content. " +
              "Must include the \\end{document} line.")
    )
    parser.add_argument(
        '--docclass',
        default=DOC_CLASS,
        help="set document class"
    )
    parser.add_argument(
        '--filename',
        default=None,
        help="input file"
    )
    args = parser.parse_args()
    if args.debug:
        logging.getLogger().setLevel(20)

    if args.filename:
        with open(args.filename) as f:
            main(args, f)
    else:
        main(args, sys.stdin)

if __name__ == '__main__':
    run()