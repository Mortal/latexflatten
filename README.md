The program `flatten.py` turns a collection of LaTeX files with conditional
compilation and assets in multiple into a **single .tex-file** with **all
assets in one folder**.

## Features

* `\input` is recognized, and all TeX output is in a single file.
* `\iffoo...\else...\fi` is parsed, and sections not compiled are removed.
* No consecutive blank lines in the output.
* Blank line inserted before all `\section`, `\subsection`, `\subsubsection`.
* `\documentclass`, `\includegraphics` and `\bibliography` are recognized
  and copied to the output folder.
* A user-specified set of macros are recognized and expanded
  (see `process_macros` in the `flatten.py`).

## Usage

`python3 flatten.py -o output master.tex`

## Limitations

In order to keep the parser simple, the input .tex files must adhere to the
following:

* `\newif\iffoo`, `\footrue`, `\foofalse` must be on their own lines,
  optionally followed by a TeX-comment.
* `\input{foo}` must be on its own line.
* `\newcommand{\foo}[1]{foo bar #1 baz}` must be on its own line,
  and whenever `\foo` is instantiated, the arguments must not contain
  (nested) curly braces; that is, usage like `\foo{a{b}c}` is not supported
  by the regex-based parser.
* `\section`, `\subsection`, `\subsubsection` must be on their own lines.
