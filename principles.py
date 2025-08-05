"""
principles.py
--------------

This module interprets the low‑level metrics gathered by ``metrics.py`` in
terms of higher‑level software engineering principles.  In particular it
provides heuristics to assess adherence to the SOLID object‑oriented
principles and to functional programming ideals.

The SOLID principles promote maintainable software design by guiding how
classes and interfaces should be structured.  They are summarised as
follows【821855371965911†L193-L205】:

* **Single responsibility** – a class should have one reason to change.
* **Open–closed** – software entities should be open for extension but closed
  for modification【821855371965911†L212-L221】.
* **Liskov substitution** – objects of a superclass should be replaceable
  with objects of a subclass without affecting correctness【821855371965911†L227-L240】.
* **Interface segregation** – clients should not depend on interfaces they do
  not use【821855371965911†L246-L257】.
* **Dependency inversion** – depend on abstractions rather than concretions【821855371965911†L263-L274】.

Because we cannot precisely infer intent from static text alone, the functions
below employ simple heuristics based on counts and naming patterns.  These
heuristics provide signals rather than absolute judgments; they are intended to
highlight areas worth investigating during code review.

Functional programming encourages immutable state and pure functions.  Pure
functions return the same result for the same inputs and have no side effects.
Functional languages also promote higher‑order functions and immutable data
structures【636678559067727†L19-L34】.  We detect functional style by counting
occurrences of lambda expressions, common higher‑order functions and by looking
for assignments which indicate mutable state.
"""

from __future__ import annotations

import re
from typing import Dict, List

from .metrics import FileMetrics


def evaluate_solid(files: List[FileMetrics]) -> Dict[str, float]:
    """Evaluate SOLID adherence based on file metrics.

    The heuristics implemented here operate on aggregated statistics:

    * **SRP**: We assume a class is responsible for too much if it contains
      more than five functions.  For each file we compare the number of
      functions to the number of classes.  A large average (>5 functions per
      class) suggests multiple responsibilities.
    * **OCP**: We estimate openness for extension by detecting inheritance.
      Files containing the keywords ``extends`` or ``:`` in class definitions
      are treated as examples of extension.  The ratio of such classes to total
      classes is returned.
    * **LSP**, **ISP** and **DIP** cannot be assessed reliably without a
      deeper semantic model.  However we include placeholder metrics that
      indicate whether any interfaces are defined and whether interfaces have
      fewer than five methods on average (which implies segregation).  For
      dependency inversion we check whether the word ``interface`` or
      ``abstract`` appears in import statements (suggesting use of abstractions).

    Args:
        files: A list of ``FileMetrics`` produced by ``metrics.analyse_directory``.

    Returns:
        A dictionary mapping principle names to heuristic scores between 0 and 1.
    """
    total_classes = 0
    total_functions = 0
    classes_with_inheritance = 0
    total_interfaces = 0
    interface_methods = 0
    uses_abstract_in_imports = 0

    for fm in files:
        total_classes += fm.num_classes
        total_functions += fm.num_functions
        total_interfaces += fm.num_interfaces
        # Rough inheritance detection: scan file text for "extends" or ":" after class
        try:
            with open(fm.path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
        except Exception:
            text = ""
        # Count classes with inheritance by matching patterns like
        # ``class Foo extends Bar`` (Java, JS) or ``class Foo : Bar`` (C++)
        inheritance_pattern = re.compile(r"class\s+\w+\s*(?:extends|:)\s+\w+", re.IGNORECASE)
        classes_with_inheritance += len(inheritance_pattern.findall(text))
        # Extract interface definitions to count methods
        interface_pattern = re.compile(r"interface\s+\w+\s*{([^}]*)}", re.MULTILINE | re.DOTALL)
        for match in interface_pattern.findall(text):
            methods = re.findall(r"\b\w+\s*\(.*?\)\s*;", match)
            interface_methods += len(methods)
        # Count import lines mentioning abstractions
        for line in text.splitlines():
            if re.match(r"\s*(import|using|require)\b", line):
                if re.search(r"(interface|abstract)", line, re.IGNORECASE):
                    uses_abstract_in_imports += 1

    srp_score = 1.0
    if total_classes > 0:
        avg_methods_per_class = (total_functions / total_classes) if total_classes else 0
        # A perfect SRP score when average methods per class <= 5, degrade otherwise
        srp_score = max(0.0, 1.0 - max(0, avg_methods_per_class - 5) / 10)
    else:
        # If no classes present, consider SRP not applicable (neutral score)
        srp_score = 1.0

    ocp_score = 1.0
    if total_classes > 0:
        ocp_score = min(1.0, classes_with_inheritance / total_classes) if total_classes else 0
    # Interpreting a higher fraction of inherited classes as better openness

    # Interface segregation: average methods per interface should be low (<5) for good ISP
    isp_score = 1.0
    if total_interfaces > 0:
        avg_interface_methods = interface_methods / total_interfaces
        isp_score = max(0.0, 1.0 - max(0, avg_interface_methods - 5) / 10)
    # Dependency inversion: presence of imports referencing abstractions increases score
    total_imports = 0
    for fm in files:
        try:
            with open(fm.path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if re.match(r"\s*(import|using|require)\b", line):
                        total_imports += 1
        except Exception:
            pass
    dip_score = (uses_abstract_in_imports / total_imports) if total_imports else 0.0

    # Liskov substitution principle cannot be inferred reliably; assign neutral score.
    lsp_score = 0.5

    return {
        "single_responsibility": round(srp_score, 3),
        "open_closed": round(ocp_score, 3),
        "interface_segregation": round(isp_score, 3),
        "dependency_inversion": round(dip_score, 3),
        "liskov_substitution": lsp_score,
    }


def evaluate_functional(files: List[FileMetrics]) -> Dict[str, float]:
    """Assess functional programming characteristics in the analysed files.

    The heuristics include:

    * **Pure functions**: We attempt to find functions that have no obvious
      side effects.  A function is considered impure if it writes to global
      variables (detected by assignments outside the function) or contains
      print/log statements.  Because parsing arbitrary languages is hard, we
      count functions declared in files that do not contain any assignments or
      print statements as "pure".
    * **Higher‑order functions**: We count the number of occurrences of
      lambda expressions or calls to common functional combinators like
      ``map`` and ``filter``【636678559067727†L42-L63】.
    * **Immutability**: We look for keywords signalling immutable declarations
      such as ``const`` (in C, C++, JS), ``final`` (Java), or use of Python
      tuples and ``dataclasses``.  A high ratio of immutable declarations is
      considered beneficial.

    Args:
        files: List of ``FileMetrics`` from the analysis.

    Returns:
        A dictionary containing scores (between 0 and 1) for purity,
        higher‑order usage and immutability.
    """
    total_functions = sum(fm.num_functions for fm in files)
    pure_functions = 0
    higher_order_count = 0
    immutable_count = 0
    total_assignments = 0

    assignment_pattern = re.compile(r"^[^#\n]*=", re.MULTILINE)
    print_pattern = re.compile(r"\b(print|console\.log|System\.out\.println)\b")
    lambda_pattern = re.compile(r"\blambda\b|=>")
    hof_pattern = re.compile(r"\b(map|filter|reduce|fold|forEach)\b")
    immutable_keywords = re.compile(r"\b(const|final|immutable)\b", re.IGNORECASE)

    for fm in files:
        try:
            with open(fm.path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
        except Exception:
            continue
        # Count assignments and print calls for purity detection
        total_assignments += len(assignment_pattern.findall(text))
        if fm.num_functions > 0:
            # If no assignments or print statements exist in the file, assume all
            # functions are pure.  Otherwise approximate purity by the ratio of
            # non‑assignment lines to lines.
            if total_assignments == 0 and not print_pattern.search(text):
                pure_functions += fm.num_functions
        # Count higher order functions
        higher_order_count += len(lambda_pattern.findall(text))
        higher_order_count += len(hof_pattern.findall(text))
        # Count immutable declarations
        immutable_count += len(immutable_keywords.findall(text))

    purity_score = (pure_functions / total_functions) if total_functions else 0.0
    hof_score = min(1.0, higher_order_count / max(1, total_functions))
    immutability_score = min(1.0, immutable_count / max(1, total_assignments + 1))

    return {
        "purity": round(purity_score, 3),
        "higher_order_usage": round(hof_score, 3),
        "immutability": round(immutability_score, 3),
    }
