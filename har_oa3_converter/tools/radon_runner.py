#!/usr/bin/env python
"""Radon wrapper for code quality metrics and duplication detection.

This module provides convenient CLI wrappers for Radon's functionality,
focusing on code duplication detection, complexity metrics, and maintainability.

It generates both console output and structured reports for CI integration.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

# Import radon modules
from radon.cli import cc, hal, mi, raw
from radon.cli.tools import iter_filenames
from radon.complexity import cc_rank, cc_visit
from radon.raw import analyze

# Set defaults that align with project standards
DEFAULT_EXCLUDE = "tests/,docs/,.venv/,dist/,build/"
DEFAULT_MIN_SIMILARITY = 0.85  # 85% similarity threshold for duplication
DEFAULT_MIN_TOKENS = 50  # Minimum token sequence to consider as duplicated
DEFAULT_REPORT_DIR = "reports/radon"


def setup_report_dir(report_dir: str = DEFAULT_REPORT_DIR) -> str:
    """Set up the report directory.

    Args:
        report_dir: Directory to store reports

    Returns:
        Path to report directory
    """
    report_path = Path(report_dir)
    report_path.mkdir(parents=True, exist_ok=True)
    return str(report_path)


def run_cc(args: Optional[List[str]] = None) -> int:
    """Run cyclomatic complexity analysis.

    Args:
        args: Command line arguments

    Returns:
        Exit code
    """
    parser = argparse.ArgumentParser(description="Run Radon CC analysis")
    parser.add_argument(
        "paths", nargs="*", default=["har_oa3_converter"], help="Paths to analyze"
    )
    parser.add_argument(
        "--exclude",
        default=DEFAULT_EXCLUDE,
        help=f"Comma-separated patterns to exclude (default: {DEFAULT_EXCLUDE})",
    )
    parser.add_argument(
        "--min",
        default="B",
        choices=["A", "B", "C", "D", "E", "F"],
        help="Minimum complexity rank to show (default: B)",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate JSON report for CI integration",
    )
    parser.add_argument(
        "--report-dir",
        default=DEFAULT_REPORT_DIR,
        help=f"Directory to store reports (default: {DEFAULT_REPORT_DIR})",
    )
    parser.add_argument(
        "--fail-on-error",
        action="store_true",
        help="Exit with non-zero code if any file exceeds complexity threshold",
    )

    parsed_args = parser.parse_args(args)
    cc_args = [
        "-s",  # Show complexity score
        "-a",  # Average complexity
        "-e",
        parsed_args.exclude,  # Exclude patterns
        "--min",
        parsed_args.min,  # Minimum rank
        "--no-assert",  # Don't count assertions
        "--total-average",  # Include total average
    ]
    cc_args.extend(parsed_args.paths)

    # Run cc analysis
    result = cc.main(cc_args)

    # Generate report if requested
    if parsed_args.report:
        report_dir = setup_report_dir(parsed_args.report_dir)
        report_file = os.path.join(report_dir, "cc_report.json")

        # Gather results
        complexity_report = {}
        for path in parsed_args.paths:
            for filename in iter_filenames([path], parsed_args.exclude.split(",")):
                with open(filename, "r", encoding="utf-8") as f:
                    source_code = f.read()
                    results = cc_visit(source_code, filename)
                    complexity_report[filename] = [
                        {
                            "name": result.name,
                            "line": result.lineno,
                            "complexity": result.complexity,
                            "rank": cc_rank(result.complexity),
                        }
                        for result in results
                    ]

        # Write report
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(complexity_report, f, indent=2)

        print(f"CC analysis report written to {report_file}")

    # Return exit code
    if parsed_args.fail_on_error and result > 0:
        return 1
    return 0


def run_mi(args: Optional[List[str]] = None) -> int:
    """Run maintainability index analysis.

    Args:
        args: Command line arguments

    Returns:
        Exit code
    """
    parser = argparse.ArgumentParser(description="Run Radon MI analysis")
    parser.add_argument(
        "paths", nargs="*", default=["har_oa3_converter"], help="Paths to analyze"
    )
    parser.add_argument(
        "--exclude",
        default=DEFAULT_EXCLUDE,
        help=f"Comma-separated patterns to exclude (default: {DEFAULT_EXCLUDE})",
    )
    parser.add_argument(
        "--min",
        default="B",
        choices=["A", "B", "C", "D", "E", "F"],
        help="Minimum maintainability rank to show (default: B)",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate JSON report for CI integration",
    )
    parser.add_argument(
        "--report-dir",
        default=DEFAULT_REPORT_DIR,
        help=f"Directory to store reports (default: {DEFAULT_REPORT_DIR})",
    )
    parser.add_argument(
        "--fail-on-error",
        action="store_true",
        help="Exit with non-zero code if any file falls below maintainability threshold",
    )

    parsed_args = parser.parse_args(args)
    mi_args = [
        "-s",  # Show more information
        "-e",
        parsed_args.exclude,  # Exclude patterns
        "--min",
        parsed_args.min,  # Minimum rank
    ]
    mi_args.extend(parsed_args.paths)

    # Run mi analysis
    result = mi.main(mi_args)

    # Generate report if requested
    if parsed_args.report:
        report_dir = setup_report_dir(parsed_args.report_dir)
        report_file = os.path.join(report_dir, "mi_report.json")

        # Gather results - since Radon's mi module doesn't provide a clean way to get structured data
        # we'll rerun the analysis to get the data
        mi_report = {}
        for path in parsed_args.paths:
            for filename in iter_filenames([path], parsed_args.exclude.split(",")):
                with open(filename, "r", encoding="utf-8") as f:
                    source_code = f.read()
                    mi_score = mi.mi_visit(source_code, multi=True)
                    mi_report[filename] = {
                        "score": mi_score,
                        "rank": mi.mi_rank(mi_score),
                    }

        # Write report
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(mi_report, f, indent=2)

        print(f"MI analysis report written to {report_file}")

    # Return exit code
    if parsed_args.fail_on_error and result > 0:
        return 1
    return 0


def run_raw(args: Optional[List[str]] = None) -> int:
    """Run raw metrics analysis.

    Args:
        args: Command line arguments

    Returns:
        Exit code
    """
    parser = argparse.ArgumentParser(description="Run Radon RAW analysis")
    parser.add_argument(
        "paths", nargs="*", default=["har_oa3_converter"], help="Paths to analyze"
    )
    parser.add_argument(
        "--exclude",
        default=DEFAULT_EXCLUDE,
        help=f"Comma-separated patterns to exclude (default: {DEFAULT_EXCLUDE})",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Include summary metrics for each file",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate JSON report for CI integration",
    )
    parser.add_argument(
        "--report-dir",
        default=DEFAULT_REPORT_DIR,
        help=f"Directory to store reports (default: {DEFAULT_REPORT_DIR})",
    )

    parsed_args = parser.parse_args(args)
    raw_args = [
        "-s",  # Summary
        "-e",
        parsed_args.exclude,  # Exclude patterns
    ]
    if parsed_args.summary:
        raw_args.append("--summary")

    raw_args.extend(parsed_args.paths)

    # Run raw analysis
    raw.main(raw_args)

    # Generate report if requested
    if parsed_args.report:
        report_dir = setup_report_dir(parsed_args.report_dir)
        report_file = os.path.join(report_dir, "raw_report.json")

        # Gather results
        raw_report = {}
        for path in parsed_args.paths:
            for filename in iter_filenames([path], parsed_args.exclude.split(",")):
                with open(filename, "r", encoding="utf-8") as f:
                    source_code = f.read()
                    raw_analysis = analyze(source_code)
                    raw_report[filename] = {
                        "loc": raw_analysis.loc,
                        "lloc": raw_analysis.lloc,
                        "sloc": raw_analysis.sloc,
                        "comments": raw_analysis.comments,
                        "single_comments": raw_analysis.single_comments,
                        "multi": raw_analysis.multi,
                        "blank": raw_analysis.blank,
                        "comment_ratio": raw_analysis.comments / raw_analysis.loc
                        if raw_analysis.loc > 0
                        else 0,
                    }

        # Write report
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(raw_report, f, indent=2)

        print(f"Raw metrics report written to {report_file}")

    return 0


def run_hal(args: Optional[List[str]] = None) -> int:
    """Run Halstead metrics analysis.

    Args:
        args: Command line arguments

    Returns:
        Exit code
    """
    parser = argparse.ArgumentParser(description="Run Radon HAL analysis")
    parser.add_argument(
        "paths", nargs="*", default=["har_oa3_converter"], help="Paths to analyze"
    )
    parser.add_argument(
        "--exclude",
        default=DEFAULT_EXCLUDE,
        help=f"Comma-separated patterns to exclude (default: {DEFAULT_EXCLUDE})",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate JSON report for CI integration",
    )
    parser.add_argument(
        "--report-dir",
        default=DEFAULT_REPORT_DIR,
        help=f"Directory to store reports (default: {DEFAULT_REPORT_DIR})",
    )

    parsed_args = parser.parse_args(args)
    hal_args = [
        "-e",
        parsed_args.exclude,  # Exclude patterns
        "--functions",  # Show metrics for each function
    ]
    hal_args.extend(parsed_args.paths)

    # Run hal analysis
    hal.main(hal_args)

    # Generate report if requested
    if parsed_args.report:
        report_dir = setup_report_dir(parsed_args.report_dir)
        report_file = os.path.join(report_dir, "hal_report.json")

        # Gather results
        hal_report = {}
        for path in parsed_args.paths:
            for filename in iter_filenames([path], parsed_args.exclude.split(",")):
                with open(filename, "r", encoding="utf-8") as f:
                    source_code = f.read()
                    hal_metrics = hal.hal_visit(source_code)
                    hal_report[filename] = [
                        {
                            "name": metric[0],
                            "line": metric[1].lineno,
                            "metrics": {
                                "h1": metric[1].total.h1,
                                "h2": metric[1].total.h2,
                                "N1": metric[1].total.N1,
                                "N2": metric[1].total.N2,
                                "vocabulary": metric[1].total.vocabulary,
                                "length": metric[1].total.length,
                                "calculated_length": metric[1].total.calculated_length,
                                "volume": metric[1].total.volume,
                                "difficulty": metric[1].total.difficulty,
                                "effort": metric[1].total.effort,
                                "time": metric[1].total.time,
                                "bugs": metric[1].total.bugs,
                            },
                        }
                        for metric in hal_metrics.items()
                    ]

        # Write report
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(hal_report, f, indent=2)

        print(f"Halstead metrics report written to {report_file}")

    return 0


def find_duplicates(args: Optional[List[str]] = None) -> int:
    """Find duplicated code in the project.

    This uses Radon's features to analyze code and find similar blocks. It looks for
    blocks with high similarity and reports them.

    Args:
        args: Command line arguments

    Returns:
        Exit code (0 for success, 1 if duplicates found and fail_on_duplicates is True)
    """
    try:
        # Import simian helper class for duplicate detection
        from radon.visitors import HalsteadVisitor
    except ImportError:
        print(
            "Error: Could not import HalsteadVisitor. Please ensure radon is installed."
        )
        return 1

    parser = argparse.ArgumentParser(description="Find duplicated code using Radon")
    parser.add_argument(
        "paths", nargs="*", default=["har_oa3_converter"], help="Paths to analyze"
    )
    parser.add_argument(
        "--exclude",
        default=DEFAULT_EXCLUDE,
        help=f"Comma-separated patterns to exclude (default: {DEFAULT_EXCLUDE})",
    )
    parser.add_argument(
        "--min-similarity",
        type=float,
        default=DEFAULT_MIN_SIMILARITY,
        help=f"Minimum similarity threshold (default: {DEFAULT_MIN_SIMILARITY})",
    )
    parser.add_argument(
        "--min-tokens",
        type=int,
        default=DEFAULT_MIN_TOKENS,
        help=f"Minimum token sequence length (default: {DEFAULT_MIN_TOKENS})",
    )
    parser.add_argument(
        "--fail-on-duplicates",
        action="store_true",
        help="Exit with non-zero code if duplicates found",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate JSON report for CI integration",
    )
    parser.add_argument(
        "--report-dir",
        default=DEFAULT_REPORT_DIR,
        help=f"Directory to store reports (default: {DEFAULT_REPORT_DIR})",
    )

    parsed_args = parser.parse_args(args)

    # Collect all Python files
    files = []
    for path in parsed_args.paths:
        files.extend(list(iter_filenames([path], parsed_args.exclude.split(","))))

    # Storage for similar code blocks found
    duplicates: List[Dict[str, Union[str, int, float, List[Tuple[str, int, str]]]]] = []

    print(f"Analyzing {len(files)} files for duplicated code...")

    # Process each file
    for i, file_path in enumerate(files):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                file_content = f.read()

            visitor = HalsteadVisitor.from_code(file_content)
            file_tokens = visitor.operators + visitor.operands

            # Compare with other files
            for j, other_file in enumerate(files[i + 1 :], start=i + 1):
                try:
                    with open(other_file, "r", encoding="utf-8") as f:
                        other_content = f.read()

                    other_visitor = HalsteadVisitor.from_code(other_content)
                    other_tokens = other_visitor.operators + other_visitor.operands

                    # Calculate similarity
                    common_tokens = set(file_tokens) & set(other_tokens)
                    if not common_tokens or not file_tokens or not other_tokens:
                        continue

                    similarity = len(common_tokens) / max(
                        len(file_tokens), len(other_tokens)
                    )

                    if (
                        similarity >= parsed_args.min_similarity
                        and len(common_tokens) >= parsed_args.min_tokens
                    ):
                        duplicates.append(
                            {
                                "file1": file_path,
                                "file2": other_file,
                                "similarity": similarity,
                                "common_tokens": len(common_tokens),
                                "total_tokens1": len(file_tokens),
                                "total_tokens2": len(other_tokens),
                            }
                        )
                except Exception as e:
                    print(f"Error analyzing {other_file}: {str(e)}")
        except Exception as e:
            print(f"Error analyzing {file_path}: {str(e)}")

    # Sort duplicates by similarity (highest first)
    duplicates.sort(key=lambda x: x["similarity"], reverse=True)

    # Output results
    if duplicates:
        print(f"\nFound {len(duplicates)} potential code duplications:")
        for i, dup in enumerate(duplicates, 1):
            print(
                f"\n{i}. Similarity: {dup['similarity']:.2f} ({dup['common_tokens']} common tokens)"
            )
            print(f"   File 1: {dup['file1']} ({dup['total_tokens1']} tokens)")
            print(f"   File 2: {dup['file2']} ({dup['total_tokens2']} tokens)")
    else:
        print("\nNo significant code duplication found.")

    # Generate report if requested
    if parsed_args.report:
        report_dir = setup_report_dir(parsed_args.report_dir)
        report_file = os.path.join(report_dir, "duplication_report.json")

        report_data = {
            "summary": {
                "files_analyzed": len(files),
                "duplicates_found": len(duplicates),
                "threshold": {
                    "min_similarity": parsed_args.min_similarity,
                    "min_tokens": parsed_args.min_tokens,
                },
            },
            "duplicates": duplicates,
        }

        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2)

        print(f"\nDuplication report written to {report_file}")

    # Return appropriate exit code
    if duplicates and parsed_args.fail_on_duplicates:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(find_duplicates())
