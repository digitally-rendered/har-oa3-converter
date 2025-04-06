# BUILD file for Bazel scripts

load("@bazel_skylib//rules:copy_file.bzl", "copy_file")

# Make the scripts available as Bazel targets
sh_binary(
    name = "build",
    srcs = ["build.sh"],
    visibility = ["//visibility:public"],
)

sh_binary(
    name = "publish",
    srcs = ["publish.sh"],
    visibility = ["//visibility:public"],
)
