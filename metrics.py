"""
metrics.py
-----------

This module provides basic static analysis routines for measuring code quality and
complexity.  The functions defined here operate on plain text source files and
make no assumptions about the underlying programming language beyond simple
syntax cues (e.g. keywords such as ``if`` or ``for``).

The goal of this module is to gather high‑level metrics that help describe a
codebase.  It is not a full parser and therefore works best on
languages with C‑like syntax or Python.  For unsupported languages the
heuristics may be less accurate, but they still provide a rough picture of
complexity and style.

Metrics collected include:

* The number of functions and classes in a file.
* An approximation of the cyclomatic complexity of the file based on decision
  keywords.  Cyclomatic complexity measures the number of linearly independent
  paths through a program's code【733509849101575†L144-L153】.  It increases with
  each branch or loop and has been shown to correlate with the risk of defects
  and testing effort.
* Violations of style guidelines such as indentation using mixed tabs and
  spaces or lines exceeding 79 characters.  Python's style guide (PEP 8) advises
  limiting lines to 79 characters to improve readability and make code easier
  to review【263717488702505†L234-L249】.
* A simple comment ratio – the number of comment lines divided by the total
  number of lines.

These metrics can be combined with higher‑level principles in
``principles.py`` to infer whether a codebase follows SOLID and functional
programming practices.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class FileMetrics:
    """A container for the metrics of a single source file."""

    path: str
    num_functions: int = 0
    num_classes: int = 0
    num_interfaces: int = 0
    cyclomatic_complexity: int = 1
    complexity_category: str = "Simple"
    line_count: int = 0
    comment_count: int = 0
    long_line_count: int = 0
    mixed_indent: bool = False
    language: str = "unknown"
    additional_info: Dict[str, float] = field(default_factory=dict)

    @property
    def comment_ratio(self) -> float:
        """Return the fraction of lines in this file that are comments."""
        if self.line_count == 0:
            return 0.0
        return self.comment_count / self.line_count

    @property
    def long_line_ratio(self) -> float:
        """Return the fraction of lines exceeding 79 characters."""
        if self.line_count == 0:
            return 0.0
        return self.long_line_count / self.line_count


def detect_language(filename: str) -> str:
    """A very naive language detector based on file extension.

    Args:
        filename: The file name or path.

    Returns:
        A string describing the language, e.g. ``'python'`` or ``'javascript'``.
    """
    ext = os.path.splitext(filename)[1].lower()
    return {
        ".py": "python",
        ".js": "javascript",
        ".java": "java",
        ".cpp": "cpp",
        ".c": "c",
        ".cs": "csharp",
        ".ts": "typescript",
        ".rb": "ruby",
        ".go": "go",
    }.get(ext, "unknown")


def count_patterns(patterns: List[str], line: str) -> int:
    """Count occurrences of any of the patterns in a line.

    The search is case sensitive and looks for whole words.  Simple regular
    expressions are used to avoid false positives (e.g. matching ``if`` inside
    ``diff``).

    Args:
        patterns: A list of keywords to search for.
        line: The line of text.

    Returns:
        The number of occurrences of any keyword in the line.
    """
    count = 0
    for kw in patterns:
        # Use word boundaries to avoid matching substrings inside other words.
        if re.search(r"\b" + re.escape(kw) + r"\b", line):
            count += 1
    return count


def analyse_file(path: str) -> Optional[FileMetrics]:
    """Analyse a single source file and return metrics.

    The function reads the file line by line.  It counts function, class and
    interface declarations using simple regular expressions, estimates
    cyclomatic complexity by counting branching keywords and loops, detects
    style violations like mixed indentation and overly long lines, and gathers
    additional lightweight statistics.

    Args:
        path: The path to the file.

    Returns:
        A ``FileMetrics`` instance with the collected data.  If the file cannot
        be read (e.g. binary files), ``None`` is returned.
    """
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except Exception:
        return None

    metrics = FileMetrics(path=path)
    metrics.language = detect_language(path)
    indent_char: Optional[str] = None  # Track whether indentation uses spaces or tabs
    complexity = 1  # baseline complexity per McCabe

    # Define patterns to look for when estimating complexity.  Each occurrence
    # adds one to the complexity count.  The list covers common decision and
    # loop constructs across several languages.
    decision_keywords = [
        "if", "elif", "else if", "for", "while", "case", "switch",
        "catch", "except", "&&", "||", "?", "and", "or",
    ]

    # Patterns for detecting function, class and interface definitions.  These
    # patterns are deliberately broad to work on multiple languages.  They
    # primarily look for lines that start with the keyword and contain an
    # opening parenthesis (for functions) or do not (for classes).
    function_patterns = [
        re.compile(r"^\s*(def|function|func|public\s+static|private\s+static|"  # Python, JS
                    r"public|private|protected|static|final)?\s*\w+\s*\(.*\)"),
    ]
    class_patterns = [
        re.compile(r"^\s*(class|struct)\b"),
    ]
    interface_patterns = [
        re.compile(r"^\s*interface\b"),
    ]

    for line in lines:
        metrics.line_count += 1
        stripped = line.strip()

        # Count comments: lines starting with comment tokens.
        if stripped.startswith("#") or stripped.startswith("//") or \
           stripped.startswith("/*") or stripped.startswith("*") or \
           stripped.startswith("--"):
            metrics.comment_count += 1

        # Track indentation style for Python; check if spaces or tabs are mixed.
        if metrics.language == "python":
            match = re.match(r"^(\s+)", line)
            if match:
                current_indent = match.group(1)
                current_char = current_indent[0]
                if indent_char is None:
                    indent_char = current_char
                elif current_char != indent_char:
                    metrics.mixed_indent = True

        # Count lines exceeding 79 characters in any language (PEP 8 suggests
        # limiting lines to 79 characters【263717488702505†L234-L249】).
        if len(line.rstrip("\n")) > 79:
            metrics.long_line_count += 1

        # Count functions/classes/interfaces using regex patterns.  We only
        # increment once per line even if multiple patterns match.
        for pattern in function_patterns:
            if pattern.match(line):
                metrics.num_functions += 1
                break
        for pattern in class_patterns:
            if pattern.match(line):
                metrics.num_classes += 1
                break
        for pattern in interface_patterns:
            if pattern.match(line):
                metrics.num_interfaces += 1
                break

        # Estimate cyclomatic complexity: add one for each decision keyword.
        complexity += count_patterns(decision_keywords, line)

    metrics.cyclomatic_complexity = complexity

    # Map complexity to risk categories based on Tom McCabe's original
    # classification【733509849101575†L249-L253】.
    if complexity <= 10:
        metrics.complexity_category = "Simple"
    elif complexity <= 20:
        metrics.complexity_category = "Moderate"
    elif complexity <= 50:
        metrics.complexity_category = "Complex"
    else:
        metrics.complexity_category = "Very High"

    return metrics


def analyse_directory(path: str, extensions: Optional[List[str]] = None) -> List[FileMetrics]:
    """Recursively analyse all source files in a directory.

    Args:
        path: Root directory to search.
        extensions: Optional list of file extensions to include.  When not
            provided, all files with a recognized language extension are
            analysed.

    Returns:
        A list of ``FileMetrics`` objects, one per analysed file.  Files that
        cannot be read or whose language is unknown are skipped.
    """
    results: List[FileMetrics] = []
    for root, _, files in os.walk(path):
        for fname in files:
            file_path = os.path.join(root, fname)
            lang = detect_language(fname)
            # Skip unknown languages unless no extension filter is provided.
            if extensions is not None:
                if not any(fname.endswith(ext) for ext in extensions):
                    continue
            else:
                if lang == "unknown":
                    continue
            metrics = analyse_file(file_path)
            if metrics is not None:
                results.append(metrics)
    return results
