"""Setup configuration for transpilation API package"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="transpilation-api",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="High-performance API for code transpilation between programming languages",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/transpilation-api",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Compilers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.11",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "black>=23.11.0",
            "ruff>=0.1.6",
            "mypy>=1.7.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "transpile-api=src.main:main",
        ],
    },
)