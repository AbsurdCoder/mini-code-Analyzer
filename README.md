# Code Analyzer

This project is a command‑line tool for gaining insight into a codebase.
It traverses a directory of source files, collects simple metrics about
functions, classes and complexity, and then interprets these metrics through
the lens of well‑known software design principles.  The aim is to help
developers understand where their code might benefit from refactoring or
improvements to structure and style.

## Background

### Complexity metrics

Cyclomatic complexity is a software metric that quantifies the number of
linearly independent paths through a program’s source code.  It is computed
using a control‑flow graph, where nodes represent groups of commands and edges
represent possible transfers of control.  A program with no branching has
complexity 1; each `if` statement increases the complexity by one path; loops
and compound conditionals add further paths.  Tom McCabe proposed
a categorisation of complexity into four risk levels: 1–10 (simple), 11–20
(moderate), 21–50 (complex) and >50 (very high risk).  High complexity
correlates with greater testing effort and risk of defects.

### Coding style

For Python code, PEP 8 provides comprehensive style guidelines.  It
recommends using four spaces per indentation level and discourages mixing
tabs and spaces.  It also advises limiting line length to 79
characters to make code easier to read and to accommodate side‑by‑side
diffs.  These conventions improve readability and facilitate code
reviews.

### SOLID principles

The SOLID acronym summarises five object‑oriented design guidelines that
improve maintainability.  The single‑responsibility principle states that a
class should have only one reason to change.  The open‑closed
principle requires that software entities be open to extension but closed
to modification, i.e. behaviour is added through composition or inheritance
without altering existing code.  The Liskov substitution principle
demands that subclasses be usable anywhere their base class is expected
without breaking correctness.  Interface segregation
advises against forcing clients to depend on methods they do not use, and
dependency inversion encourages modules to depend on abstractions rather than
concrete implementations.

### Functional programming

Functional programming treats computation as the evaluation of mathematical
functions and emphasises pure functions, immutability and higher‑order
functions.  Pure functions take inputs and return outputs without side
effects, making programs easier to reason about.  The paradigm also
encourages the use of `map`, `filter`, `reduce` and lambda expressions to
compose behaviour.

## Features

The analyser computes for each source file:

* **Language detection** – based on file extension.
* **Function, class and interface counts** – determined by simple regular
  expressions.  These counts give an idea of a file’s structure.
* **Cyclomatic complexity (approximate)** – calculated by scanning for
  branching keywords such as `if`, `for`, `while` and logical operators; the
  result is categorised using McCabe’s risk thresholds.
* **Style checks** – the number of lines exceeding 79 characters and whether
  Python files mix tabs and spaces.  A comment ratio is also
  reported.

After collecting these low‑level metrics the tool synthesises them into
higher‑level insights:

* **SOLID heuristic scores** – estimating whether classes have a single
  responsibility (few methods), how often inheritance is used (openness for
  extension), whether interfaces are small (segregation), and whether imports
  reference abstractions (dependency inversion).  Liskov substitution is
  assigned a neutral score because static analysis cannot easily infer it.
* **Functional programming scores** – ratios of pure functions (no assignments
  or print statements), occurrences of higher‑order constructs (lambda,
  `map`, `filter`, `reduce`) and keywords denoting immutability such as
  `const`, `final` or `immutable`.

## Usage

Ensure you have Python 3 installed.  From within the project directory, you
can run the analyser as follows:

```sh
python3 -m code_analyzer.main --path PATH/TO/SOURCE [--json results.json] [--extensions .py .js ...]
```

* ``--path`` (required): the directory to analyse.
* ``--json`` (optional): write the results to a JSON file for further
  processing.
* ``--extensions`` (optional): a list of file extensions to include.  If not
  provided, common programming language extensions (Python, JavaScript, Java,
  C, C++, C#, TypeScript, Go and Ruby) are analysed.

The tool prints a human‑readable report detailing per‑file statistics and
overall summaries, followed by SOLID and functional scores on a scale from
0 (worst) to 1 (best).

## Limitations

This project is intentionally simple.  It does **not** parse code fully and
therefore cannot understand scopes, data types or dynamic behaviour.  All
metrics and principle evaluations are approximations intended to highlight
potential issues rather than provide definitive judgments.  For more accurate
analysis, consider using language‑specific static analysers (e.g. linters,
SonarQube) and manual code reviews.
