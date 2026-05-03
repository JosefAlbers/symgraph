from setuptools import setup

setup(
    name="symgraph",
    url='https://github.com/JosefAlbers/symgraph',
    author_email="albersj66@gmail.com",
    author="J Joe",
    license="Apache-2.0",
    version="0.0.1a0",
    readme="README.md",
    description="Static analysis engine that maps Python codebases into a queryable property graph by resolving symbol definitions, inferring types, and tracing call/reference relationships.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    python_requires=">=3.11",
    install_requires=[],
    py_modules=["main"],
    entry_points={"console_scripts": ["symgraph=main:main"]},
)
