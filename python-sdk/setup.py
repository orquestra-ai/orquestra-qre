from setuptools import setup, find_packages
import os

# Function to read the README file.
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name="orquestra-sdk",
    version="0.1.0",
    author="Orquestra Development Team",
    author_email="contact@orquestra.dev", # Placeholder email
    description="Python SDK for Orquestra Quantum Resource Estimation Platform",
    long_description=read('README.md') if os.path.exists('README.md') else "Python SDK for Orquestra Quantum Resource Estimation Platform. See GitHub for more details.",
    long_description_content_type="text/markdown",
    url="https://github.com/Factory-AI/factory-tutorial/tree/main/python-sdk", # Placeholder URL, update to actual SDK repo if different
    project_urls={
        "Bug Tracker": "https://github.com/Factory-AI/factory-tutorial/issues",
        "Documentation": "https://github.com/Factory-AI/factory-tutorial/blob/main/python-sdk/README.md", # Placeholder
        "Source Code": "https://github.com/Factory-AI/factory-tutorial/tree/main/python-sdk",
    },
    packages=find_packages(exclude=["tests*", "*.tests", "*.tests.*", "tests"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Hardware :: Hardware Drivers", # Relevant for hardware manufacturer integration
    ],
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.20", # For numerical computations, matrix operations
        "scipy>=1.7",  # For advanced math, optimization, stats if needed later
        "requests>=2.25", # For potential API interactions with an Orquestra service
        "pydantic>=1.10,<3.0", # For data validation and settings management
        "typing_extensions>=4.0; python_version<'3.9'", # For newer typing features on older Python
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "flake8>=3.9",
            "mypy>=0.900",
            "black>=22.0",
            "isort>=5.0",
            "tox",
            "sphinx",
            "sphinx-rtd-theme",
        ],
        "qiskit": ["qiskit>=0.40.0"], # Optional dependency for Qiskit integration
        "cirq": ["cirq-core>=1.0.0"],   # Optional dependency for Cirq integration
        "braket": ["amazon-braket-sdk>=1.40.0"], # Optional dependency for Amazon Braket
        # Add other provider SDKs as optional dependencies
    },
    keywords="quantum computing, resource estimation, quantum hardware, sdk, orquestra",
    include_package_data=True, # To include non-code files specified in MANIFEST.in
    zip_safe=False,
)
