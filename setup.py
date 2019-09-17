import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="dbbackup",
    version="0.0.1",
    author="David Lefever",
    author_email="lefever.d@gmail.com",
    description="A database backup cli",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitlab.com/lefeverd/docker-db-backup",
    packages=setuptools.find_packages(),
    python_requires='>=3.6',
)
