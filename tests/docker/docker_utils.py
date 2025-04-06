"""Utilities for Docker testing in the har-oa3-converter project."""

import random
import string
import subprocess
import time
from typing import Optional

# Lists for generating random container names
ADJECTIVES = [
    "swift",
    "bright",
    "calm",
    "eager",
    "fair",
    "gentle",
    "happy",
    "jolly",
    "kind",
    "lively",
    "mighty",
    "noble",
    "proud",
    "quiet",
    "rapid",
    "sunny",
    "witty",
    "zealous",
    "brave",
    "clever",
    "daring",
    "elegant",
    "fierce",
    "vivid",
    "wise",
    "bold",
    "crisp",
]

NOUNS = [
    "apple",
    "breeze",
    "cloud",
    "dream",
    "eagle",
    "flower",
    "garden",
    "harbor",
    "iris",
    "journey",
    "kite",
    "lake",
    "meadow",
    "nest",
    "ocean",
    "path",
    "quilt",
    "river",
    "star",
    "tree",
    "valley",
    "wave",
    "zenith",
    "dawn",
    "forest",
    "mountain",
    "sunset",
    "thunder",
]


def generate_random_container_name(prefix: str = "har-oa3") -> str:
    """
    Generate a random container name with format prefix-adjective-noun-timestamp-random.

    This ensures uniqueness across test runs and avoids container name conflicts.

    Args:
        prefix: The prefix to use for the container name

    Returns:
        A unique container name string
    """
    timestamp = int(time.time())
    adjective = random.choice(ADJECTIVES)
    noun = random.choice(NOUNS)
    random_suffix = "".join(random.choices(string.ascii_lowercase, k=4))

    return f"{prefix}-{adjective}-{noun}-{timestamp}-{random_suffix}"


def docker_available() -> bool:
    """
    Check if Docker is available and running.

    Returns:
        True if Docker is available, False otherwise
    """
    try:
        # Run with a short timeout to quickly detect if docker is not running
        subprocess.run(
            ["docker", "info"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5,
            check=True,
        )
        return True
    except (subprocess.SubprocessError, subprocess.TimeoutExpired):
        return False


def cleanup_container(container_name: Optional[str] = None) -> bool:
    """
    Attempt to clean up a Docker container.

    Args:
        container_name: The name of the container to clean up

    Returns:
        True if cleanup was successful, False otherwise
    """
    if not container_name:
        return False

    try:
        # Check if container exists
        result = subprocess.run(
            [
                "docker",
                "ps",
                "-a",
                "--filter",
                f"name={container_name}",
                "--format",
                "{{{{.Names}}}}",
            ],
            capture_output=True,
            text=True,
        )

        if container_name in result.stdout:
            # Container exists, remove it
            subprocess.run(
                ["docker", "rm", "-f", container_name], capture_output=True, check=True
            )
            return True
    except Exception as e:
        print(f"Error cleaning up container {container_name}: {e}")

    return False
