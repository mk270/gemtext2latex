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
import gemini_url
from typing import (Optional, Generator, Callable, TypeVar, Type, TextIO,
                    List, Any)

DOC_CLASS='mk-plain'

DOC_TOP = '''
\\begin{document}
'''

DOC_TAIL = '''
\\end{document}
'''

# TODO deal with underscores being naively quoted
def italicise(delim: Optional[str], line: str) -> str:
    if delim is None:
        return line

    occurrences = line.count(delim)
    balanced = occurrences % 2 == 0
    if not balanced:
        return line

    quote = {
        "*": "\*",
    }
    quoted_delim = quote.get(delim, delim)
    pattern = re.compile(quoted_delim + "([a-zA-Z0-9, '-]*?)" + quoted_delim)
    result = re.sub(pattern, "\\\\textit\x7b\\1\x7d", line)
    return result

def latex_quote(s: str, italics_char: Optional[str]) -> str:
    pattern = r'([%$}{_#&])' # characters that latex wants to quote
    replacer = lambda x: "\\" + x.groups(0)[0]
    naive_quoted = re.sub(pattern, replacer, s)
    return italicise(italics_char, naive_quoted)


class Section:
    def __init__(self, line: str) -> None:
        self.line = line

    def __repr__(self) -> str:
        s = latex_quote(self.line, None)
        c = self.__class__.__name__
        return f"{c}: {s}\n"


class Heading(Section):
    def __init__(self, line: str):
        level = len(line.split(" ", 2)[0])
        self.line = line[level:].lstrip(" ")
        self.level = level

    def __repr__(self) -> str:
        level = "sub" * (self.level - 1)
        cmd = f"\x5c{level}section*"
        s = latex_quote(self.line, None)
        return f"{cmd}\x7b{s}\x7d\n"


class Preformatted(Section):
    def __init__(self, _line: str):
        self.lines: List[str] = []

    def __repr__(self) -> str:
        top = "\\begin{verbatim}\n"
        tail = "\n\\end{verbatim}\n"
        lines = "\n".join(self.line)
        return f"{top}{lines}{tail}"

    def append(self, line: str) -> None:
        self.lines.append(line)


class Link(Section):
    def __init__(self, line: str, base_url: str):
        relevant = line[3:]
        parts = relevant.split(" ", 1)
        self.caption = None
        if len(parts) > 1:
            self.caption = parts[1]
        self.referent = gemini_url.gemini_urljoin(base_url, parts[0])

    def __repr__(self) -> str:
        if self.caption is not None:
            return "\\href{%s}{%s}" % (self.referent, self.caption)
        return "\\url{%s}" % self.referent


class Container(Section):
    pass


# yes, I am well aware this should be factored together with
# the BulletList class below.  I don't care
class Links(Container):
    def __init__(self, i: Link):
        self.items = [i]

    def append(self, i: Link) -> None:
        self.items.append(i)

    def __repr__(self) -> str:
        top = "\\begin{itemize}\n"
        tail = "\n\\end{itemize}\n"
        items = "\n".join([ "\\item " + i.__repr__() for i in self.items ])

        return f"{top}{items}{tail}"


class Item(Section):
    def __init__(self, line: str, italics_char: str):
        self.line = line[2:]
        self.italics_char = italics_char

    def __repr__(self) -> str:
        return latex_quote(self.line, self.italics_char)


class Paragraph(Section):
    def __init__(self, line: str, italics_char: str):
        self.line = line
        self.italics_char = italics_char

    def __repr__(self) -> str:
        s = latex_quote(self.line, self.italics_char)
        return f"{s}\n"


class BulletList(Container):
    def __init__(self, i: Item):
        self.items = [i]

    def append(self, i: Item) -> None:
        self.items.append(i)

    def __repr__(self) -> str:
        top = "\\begin{itemize}\n"
        tail = "\n\\end{itemize}\n"
        items = "\n".join([ "\\item " + i.__repr__() for i in self.items ])

        return f"{top}{items}{tail}"


SectionStream = Generator[Section, None, None]


def sections(args: argparse.Namespace,
             input_stream: TextIO) -> SectionStream:
    """Get the various sections of the text:
       links, paragraphs, headings, preformatted.
    """

    def fragments() -> SectionStream:
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
                yield Link(line, args.base)

            elif line.startswith("* "):
                yield Item(line, args.italics_char)

            else:
                yield Paragraph(line, args.italics_char)

    # We can't type some of the arguments for this, so use Any
    def group_fragments(
            source: Callable[[], SectionStream],
            member_class: Any,
            group_class: Any
    ) -> SectionStream:
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
    def fragments_with_item_lists() -> SectionStream:
        for frag in group_fragments(fragments, Item, BulletList):
            yield frag

    def fragments_with_all_lists() -> SectionStream:
        for frag in group_fragments(fragments_with_item_lists, Link, Links):
            yield frag

    for frag in fragments_with_all_lists():
        yield frag


def main(args: argparse.Namespace, input_stream: TextIO) -> None:
    print("\\documentclass{%s}" % args.docclass)
    print(f"{args.top}")
    for sect in sections(args, input_stream):
        print(f"{sect}")
    print(f"{args.tail}")

def run() -> None:
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
        '--italics-char',
        default=None,
        type=str,
        help=("set the delimiter for italics")
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
    parser.add_argument(
        '--base',
        default=None,
        help=" base for use with relative URLs"
    )
    args = parser.parse_args()
    if args.debug:
        logging.getLogger().setLevel(20)

    if args.italics_char is not None:
        assert len(args.italics_char) == 1

    if args.filename:
        with open(args.filename) as f:
            main(args, f)
    else:
        main(args, sys.stdin)

if __name__ == '__main__':
    run()
