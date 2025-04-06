workspace(name = "har_oa3_converter")

load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

# Python rules for Bazel
http_archive(
    name = "rules_python",
    sha256 = "0a8003b044294d7840ac7d9d73eef05d6ceb682d7516781a4ec62d3ec6a83a43",
    strip_prefix = "rules_python-0.24.0",
    url = "https://github.com/bazelbuild/rules_python/archive/refs/tags/0.24.0.tar.gz",
)

# Load Python rules
load("@rules_python//python:repositories.bzl", "python_register_toolchains")

# Register a specific Python version
python_register_toolchains(
    name = "python3_9",
    python_version = "3.9",
)

# Load the Poetry rules repository
http_archive(
    name = "rules_poetry",
    sha256 = "da2502e5fc629b7ef195a1d53c867a87dfd18bf58ee3fde452bdb4e3a5f65c8f",
    strip_prefix = "rules_poetry-0.7.1",
    url = "https://github.com/soniaai/rules_poetry/archive/refs/tags/v0.7.1.tar.gz",
)

# Load Poetry rules
load("@rules_poetry//poetry:dependencies.bzl", "poetry_dependencies")
poetry_dependencies()
