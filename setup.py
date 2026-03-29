"""Setup script for WebMainBench."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="webmainbench",
    version="0.1.0",
    author="WebMainBench Team",
    author_email="chupei@pjlab.org.cn",
    description="A comprehensive benchmark for web main content extraction",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/opendatalab/WebMainBench",
    packages=find_packages(),
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
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Markup :: HTML",
    ],
    python_requires=">=3.8",
    install_requires=[
        "lxml>=5.3.0",
        "jsonlines>=3.1.0",
        "requests>=2.28.0",
        "beautifulsoup4>=4.12.0",
        "numpy>=1.21.0,<2.0.0",  # 避免NumPy 2.x兼容性问题
        "rapidfuzz>=3.0.0",  # 用于文本编辑距离计算
        "apted>=1.0.3",  # 用于树编辑距离计算（TEDS）
        "jieba>=0.42.0",  # 用于中文分词
        "rouge>=1.0.0",  # 用于 ROUGE 指标
    ],
    extras_require={
        "all": [
            "nltk>=3.8",
            "rouge-score>=0.1.2",
            "unstructured>=0.10.0",
        ],
        "llm": [
            "torch==2.6.0",
            "transformers==4.52.4",
            "vllm==0.8.5.post1",
            "llm_web_kit>=3.0.0",
        ],
        "nlp": [
            "nltk>=3.8",
            "rouge-score>=0.1.2",
        ],
        "unstructured": [
            "unstructured>=0.10.0",
        ],
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
            "black>=22.0",
            "isort>=5.0",
            "flake8>=5.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "webmainbench=webmainbench.cli:main",
        ],
    },
) 