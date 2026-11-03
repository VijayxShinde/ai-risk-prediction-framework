"""
Setup configuration for AI-Driven Risk Prediction Framework
Defines package metadata, dependencies, and installation configuration.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of README.md
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="ai-risk-prediction-framework",
    version="2.1.0",
    author="Risk AI Team",
    description="AI-Driven Risk Prediction Framework with Phase 2 Advanced Analytics",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/VijayxShinde/ai-risk-prediction-framework",
    packages=find_packages(where=".", include=["src*", "tests*"]),
    python_requires=">=3.9",
    install_requires=[
        "numpy",
        "pandas",
        "scikit-learn",
        "xgboost==2.1.4",
        "prophet",
        "shap",
        "spacy",
        "streamlit",
        "fastapi",
        "streamlit-shadcn-ui==0.1.19",
        "streamlit-extras==1.3.0",
        "plotly==6.6.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov",
            "black",
            "flake8",
            "mypy",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    keywords="risk prediction AI/ML forecasting anomaly-detection",
)
