from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="job-instruction-downloader",
    version="1.0.0",
    author="CoreTwin",
    author_email="info@coretwin.com",
    description="Universal application for automating document downloads from various web resources",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/CoreTwin/web2-parser-py",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.12",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "job-downloader=job_instruction_downloader.src.main:main",
        ],
    },
)
