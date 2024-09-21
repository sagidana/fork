from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read()

setup(
    name = 'fork',
    version = '0.0.1',
    author = 'Sagi Dana',
    author_email = 'sagidana1@gmail.com',
    license = 'MIT License',
    description = 'fork editor',
    long_description = long_description,
    long_description_content_type = "text/markdown",
    url = 'https://github.com/sagidana/Editor',
    packages = find_packages(),
    include_package_data=True,
    install_requires = [requirements],
    python_requires='>=3.11',
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "Operating System :: OS Independent",
    ],
    entry_points = {'console_scripts': "fork=fork:main"}
)
