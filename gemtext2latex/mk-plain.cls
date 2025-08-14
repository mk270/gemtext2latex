% On a UNIX-like, this would be installed somewhere like:
% ~/texmf/tex/latex/mk-plain.cls

\ProvidesClass{mk-plain}[2021/10/22 v1.0 Plain documents]
\NeedsTeXFormat{LaTeX2e}

\DeclareOption*{\PassOptionsToClass{\CurrentOption}{article}}
\ProcessOptions\relax

\LoadClass{article}

\usepackage[T1]{fontenc}
\usepackage[osf]{mathpazo}
\usepackage{parskip}
\usepackage{enumitem}

\usepackage[hidelinks,colorlinks=true,linkcolor=blue,urlcolor=blue]{hyperref}
