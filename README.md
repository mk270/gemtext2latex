gemtext2latex
=============

This is a trivial tool for converting text in Gemini format to LaTeX. It assumes the presence of a minimal LaTeX class called `mk-plain`.

The tool simply reads Gemini text on stdin and emits a reasonable LaTeX document, which in turn can produce a reasonable PDF via `pdflatex`. At some point, there'll be a sort of `--output pdflatex` option but that doesn't exist yet.

Usage
-----

    $ gemtext2latex < example.gemini > example.tex
    $ pdflatex example.tex

Installers
----------

It is intended that one should be able to install this via Python's normal packaging tools, e.g.,

    $ pipx install gemtext2latex

Alternatively, binary installers are going to be generated on Github. These probably install all of Python, so are a bit of overkill.

To do
-----

* provide docs
* tidy up the code

Licence
-------

To the extent that such a small piece of code is subject to copyright, I am
happy to make it available under the Apache Software Licence, v2.0.
