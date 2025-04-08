#!/usr/bin/env python
"""
Generate a coverage badge for the README.

This script parses the coverage report and generates a badge SVG file.
"""

import os
import re
import sys
from pathlib import Path

# Colors for different coverage levels
COLORS = {
    "excellent": "#4c1",  # >= 90%
    "good": "#97CA00",  # >= 80%
    "acceptable": "#dfb317",  # >= 70%
    "low": "#fe7d37",  # >= 60%
    "critical": "#e05d44",  # < 60%
}


def get_coverage_percentage():
    """Extract coverage percentage from coverage report."""
    try:
        # Try to read from coverage.xml
        coverage_file = Path("coverage.xml")
        if coverage_file.exists():
            content = coverage_file.read_text()
            match = re.search(r'line-rate="([\d.]+)"', content)
            if match:
                return float(match.group(1)) * 100

        # Fallback: run pytest with coverage
        import subprocess

        result = subprocess.run(
            ["poetry", "run", "pytest", "--cov=har_oa3_converter", "--cov-report=term"],
            capture_output=True,
            text=True,
        )

        # Parse the output to find the total coverage percentage
        for line in result.stdout.split("\n"):
            if "TOTAL" in line:
                # Extract the last percentage value
                match = re.search(r"(\d+)%$", line.strip())
                if match:
                    return int(match.group(1))
    except Exception as e:
        print(f"Error getting coverage: {e}", file=sys.stderr)
        return 0

    return 0


def get_color(percentage):
    """Get the appropriate color based on coverage percentage."""
    if percentage >= 90:
        return COLORS["excellent"]
    elif percentage >= 80:
        return COLORS["good"]
    elif percentage >= 70:
        return COLORS["acceptable"]
    elif percentage >= 60:
        return COLORS["low"]
    else:
        return COLORS["critical"]


def generate_badge(percentage):
    """Generate SVG badge content."""
    color = get_color(percentage)

    # SVG template for the badge
    svg = f"""
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="108" height="20" role="img" aria-label="coverage: {percentage}%">
  <title>coverage: {percentage}%</title>
  <linearGradient id="s" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <clipPath id="r">
    <rect width="108" height="20" rx="3" fill="#fff"/>
  </clipPath>
  <g clip-path="url(#r)">
    <rect width="63" height="20" fill="#555"/>
    <rect x="63" width="45" height="20" fill="{color}"/>
    <rect width="108" height="20" fill="url(#s)"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" text-rendering="geometricPrecision" font-size="110">
    <text aria-hidden="true" x="325" y="150" fill="#010101" fill-opacity=".3" transform="scale(.1)" textLength="530">coverage</text>
    <text x="325" y="140" transform="scale(.1)" fill="#fff" textLength="530">coverage</text>
    <text aria-hidden="true" x="850" y="150" fill="#010101" fill-opacity=".3" transform="scale(.1)" textLength="350">{percentage}%</text>
    <text x="850" y="140" transform="scale(.1)" fill="#fff" textLength="350">{percentage}%</text>
  </g>
</svg>
""".strip()

    return svg


def main():
    """Main function to generate and save the badge."""
    # Create badges directory if it doesn't exist
    badges_dir = Path("badges")
    badges_dir.mkdir(exist_ok=True)

    # Get coverage percentage
    percentage = int(get_coverage_percentage())
    print(f"Current coverage: {percentage}%")

    # Generate badge
    badge_svg = generate_badge(percentage)

    # Save badge
    badge_path = badges_dir / "coverage.svg"
    badge_path.write_text(badge_svg)
    print(f"Badge saved to {badge_path}")

    # Update README if needed
    readme_path = Path("README.md")
    if readme_path.exists():
        readme_content = readme_path.read_text()

        # Check if we need to update the codecov badge
        if "[![codecov]" in readme_content:
            print("README already has codecov badge, no need to update")
        else:
            print("Adding coverage badge to README")
            # Add badge after the title
            new_badge = f"[![coverage](https://raw.githubusercontent.com/digitally-rendered/har-oa3-converter/main/badges/coverage.svg)](.github/workflows/coverage-report.yml)"
            # Insert after the existing badges
            if "[![" in readme_content:
                pattern = r"(\[!\[[^\]]+\]\([^\)]+\)\]\([^\)]+\)\s*\n)"
                last_badge_match = list(re.finditer(pattern, readme_content))[-1]
                pos = last_badge_match.end()
                readme_content = (
                    readme_content[:pos] + new_badge + "\n" + readme_content[pos:]
                )
                readme_path.write_text(readme_content)
                print("Added coverage badge to README")


if __name__ == "__main__":
    main()
