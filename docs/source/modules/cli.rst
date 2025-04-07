CLI Module
=========

.. py:module:: har_oa3_converter.cli

The CLI module provides command-line interfaces for the HAR to OpenAPI 3 converter.

har2oa3 CLI
---------

.. py:module:: har_oa3_converter.cli.har_to_oas_cli

This module provides the main command-line interface for converting HAR files to OpenAPI 3 specifications.

.. py:function:: parse_args(args=None)

   Parse command-line arguments for the har2oa3 CLI tool.

   :param list args: Command-line arguments, or None to use sys.argv
   :return: Parsed arguments
   :rtype: argparse.Namespace

.. py:function:: main(args=None)

   Main entry point for the har2oa3 CLI tool.

   :param list args: Command-line arguments, or None to use sys.argv
   :return: Exit code (0 for success, non-zero for failure)
   :rtype: int

format-converter CLI
-----------------

.. py:module:: har_oa3_converter.cli.format_cli

This module provides a more flexible command-line interface for converting between different API formats.

.. py:function:: parse_args(args=None)

   Parse command-line arguments for the format-converter CLI tool.

   :param list args: Command-line arguments, or None to use sys.argv
   :return: Parsed arguments
   :rtype: argparse.Namespace

.. py:function:: main(args=None)

   Main entry point for the format-converter CLI tool.

   :param list args: Command-line arguments, or None to use sys.argv
   :return: Exit code (0 for success, non-zero for failure)
   :rtype: int
