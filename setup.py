from setuptools import setup, find_packages

setup(
    name = 'fork',
    version = '0.0.1',
    author = 'Sagi Dana',
    author_email = 'sagidana1@gmail.com',
    license = 'MIT License',
    description = 'fork editor',
    long_description = open("README.md", "r", encoding="utf-8").read(),
    long_description_content_type = "text/markdown",
    url = 'https://github.com/sagidana/Editor',
    packages = find_packages(),
    include_package_data=True,
    install_requires = [open("requirements.txt", "r", encoding="utf-8").read()],
    python_requires='>=3.11',
    entry_points = {'console_scripts': "fork=fork:main"}
)
