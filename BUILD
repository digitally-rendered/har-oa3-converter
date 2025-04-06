load("@rules_python//python:defs.bzl", "py_binary", "py_library", "py_test")
load("@rules_poetry//poetry:poetry.bzl", "poetry")

# Load the Poetry dependencies from pyproject.toml
poetry(
    name = "har-oa3-converter-deps",
    pyproject_toml = ":pyproject.toml",
    poetry_lock = ":poetry.lock",
)

# Main library target
py_library(
    name = "har_oa3_converter_lib",
    srcs = glob(["har_oa3_converter/**/*.py"]),
    imports = ["."],
    deps = [
        ":har-oa3-converter-deps",
    ],
)

# CLI binaries
py_binary(
    name = "har2oa3",
    srcs = ["har_oa3_converter/cli/har_to_oas_cli.py"],
    main = "har_oa3_converter/cli/har_to_oas_cli.py",
    imports = ["."],
    deps = [
        ":har_oa3_converter_lib",
    ],
)

py_binary(
    name = "api-convert",
    srcs = ["har_oa3_converter/cli/format_cli.py"],
    main = "har_oa3_converter/cli/format_cli.py",
    imports = ["."],
    deps = [
        ":har_oa3_converter_lib",
    ],
)

py_binary(
    name = "api-server",
    srcs = ["har_oa3_converter/api/server.py"],
    main = "har_oa3_converter/api/server.py",
    imports = ["."],
    deps = [
        ":har_oa3_converter_lib",
    ],
)

# Tests
py_test(
    name = "test_converters",
    srcs = glob(["tests/converters/**/*.py"]),
    imports = ["."],
    deps = [
        ":har_oa3_converter_lib",
        ":har-oa3-converter-deps",
    ],
)

py_test(
    name = "test_cli",
    srcs = glob(["tests/cli/**/*.py"]),
    imports = ["."],
    deps = [
        ":har_oa3_converter_lib",
        ":har-oa3-converter-deps",
    ],
)

py_test(
    name = "test_api",
    srcs = glob(["tests/api/**/*.py"]),
    imports = ["."],
    deps = [
        ":har_oa3_converter_lib",
        ":har-oa3-converter-deps",
    ],
)
