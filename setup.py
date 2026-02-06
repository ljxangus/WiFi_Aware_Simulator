"""Setup configuration for Wi-Fi Aware Simulator."""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="wifi-aware-simulator",
    version="1.0.0",
    author="Wi-Fi Aware Simulator Team",
    description="High-fidelity Wi-Fi Aware (NAN) Protocol Simulator based on SimPy",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/WiFi_Aware_Simulator",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Simulation",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.10",
    install_requires=[
        "simpy>=4.0.1",
        "pyyaml>=6.0",
        "numpy>=1.24.0",
        "pandas>=2.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "wifi-aware-sim=core.simulation:main",
        ],
    },
)
