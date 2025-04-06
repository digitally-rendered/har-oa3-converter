#!/bin/bash

set -e

# Navigate to project root
cd "$(dirname "$0")/.." || exit 1

# Build the Docker image
docker build -t har-oa3-converter:latest .

echo "\nDocker image 'har-oa3-converter:latest' built successfully\n"
echo "To run the converter with Docker, use:\n"
echo "docker run --rm -v \$(pwd):/data har-oa3-converter:latest <command> [options]\n"
echo "Example:\n"
echo "docker run --rm -v \$(pwd):/data har-oa3-converter:latest format -i /data/sample.har -o /data/output.yaml\n"
