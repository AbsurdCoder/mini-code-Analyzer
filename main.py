"""
main.py
-------

Command‑line interface for the Code Analyzer project.  Run this module as
a script to analyse a directory of source files and report high‑level
statistics on complexity, coding style and adherence to software design
principles.

Usage::

    python3 -m code_analyzer.main --path path/to/source [--json output.json]

The analysis operates recursively on the provided directory.  Only files with
known extensions are considered (Python, JavaScript, Java, C, C++, C#, TypeScript,
Go and Ruby by default).  Use the ``--extensions`` option to specify
additional extensions.

Example::

    python3 -m code_analyzer.main --path my_project --extensions .py .js

This will analyse all Python and JavaScript files in ``my_project``.

"""

from __future__ import annotations

import argparse
import json
import os
from typing import List

from .metrics import FileMetrics, analyse_directory
from .principles import evaluate_solid, evaluate_functional


def human_readable_summary(files: List[FileMetrics]) -> str:
    """Create a human readable summary string for the analysis.

    Args:
        files: List of file metrics.

    Returns:
        A formatted string describing per‑file metrics and overall statistics.
    """
    lines: List[str] = []
    total_functions = sum(fm.num_functions for fm in files)
    total_classes = sum(fm.num_classes for fm in files)
    total_complexity = sum(fm.cyclomatic_complexity for fm in files)
    total_files = len(files)
    total_lines = sum(fm.line_count for fm in files)
    total_comments = sum(fm.comment_count for fm in files)
    total_long_lines = sum(fm.long_line_count for fm in files)
    mixed_indent_files = sum(1 for fm in files if fm.mixed_indent)

    lines.append("\nAnalysis Summary:\n" + "=" * 70)
    for fm in files:
        lines.append(f"File: {fm.path}")
        lines.append(f"  Language               : {fm.language}")
        lines.append(f"  Functions              : {fm.num_functions}")
        lines.append(f"  Classes                : {fm.num_classes}")
        lines.append(f"  Interfaces             : {fm.num_interfaces}")
        lines.append(f"  Cyclomatic Complexity  : {fm.cyclomatic_complexity} ({fm.complexity_category})")
        lines.append(f"  Lines                  : {fm.line_count}")
        lines.append(f"  Comment lines          : {fm.comment_count} ({fm.comment_ratio:.2%})")
        lines.append(f"  Long (>79 chars) lines : {fm.long_line_count} ({fm.long_line_ratio:.2%})")
        if fm.language == "python":
            lines.append(f"  Mixed indentation      : {'Yes' if fm.mixed_indent else 'No'}")
        lines.append("")

    avg_complexity = (total_complexity / total_files) if total_files else 0
    avg_functions_per_file = (total_functions / total_files) if total_files else 0
    avg_classes_per_file = (total_classes / total_files) if total_files else 0
    comment_ratio = (total_comments / total_lines) if total_lines else 0
    long_line_ratio = (total_long_lines / total_lines) if total_lines else 0

    lines.append("Overall Statistics:\n" + "-" * 70)
    lines.append(f"Total files analysed      : {total_files}")
    lines.append(f"Total functions           : {total_functions}")
    lines.append(f"Total classes             : {total_classes}")
    lines.append(f"Average complexity        : {avg_complexity:.2f}")
    lines.append(f"Average functions/file    : {avg_functions_per_file:.2f}")
    lines.append(f"Average classes/file      : {avg_classes_per_file:.2f}")
    lines.append(f"Overall comment ratio     : {comment_ratio:.2%}")
    lines.append(f"Overall long line ratio   : {long_line_ratio:.2%}")
    lines.append(f"Files with mixed indent   : {mixed_indent_files}\n")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyse source code for complexity, style and design principles.")
    parser.add_argument("--path", required=True, help="Directory path to analyse")
    parser.add_argument("--json", help="Save analysis results to a JSON file")
    parser.add_argument("--extensions", nargs="*", help="List of file extensions to include (e.g. .py .js)")
    args = parser.parse_args()

    if not os.path.isdir(args.path):
        raise SystemExit(f"Error: path '{args.path}' does not exist or is not a directory")

    files: List[FileMetrics] = analyse_directory(args.path, extensions=args.extensions)
    if not files:
        print("No source files found to analyse.")
        return

    # Evaluate principles
    solid_scores = evaluate_solid(files)
    functional_scores = evaluate_functional(files)

    # Print summary
    print(human_readable_summary(files))
    print("SOLID principle scores (0 = poor, 1 = excellent):")
    for principle, score in solid_scores.items():
        print(f"  {principle.replace('_', ' ').title():25}: {score:.3f}")
    print("Functional programming scores (0 = poor, 1 = excellent):")
    for metric, score in functional_scores.items():
        print(f"  {metric.replace('_', ' ').title():25}: {score:.3f}")

    # Optionally write JSON
    if args.json:
        data = {
            "files": [fm.__dict__ for fm in files],
            "solid_scores": solid_scores,
            "functional_scores": functional_scores,
        }
        try:
            with open(args.json, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            print(f"\nResults written to {args.json}")
        except Exception as exc:
            print(f"Failed to write JSON file: {exc}")


if __name__ == "__main__":
    main()
