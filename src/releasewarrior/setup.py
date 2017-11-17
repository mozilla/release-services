from setuptools import setup, find_packages

version = open("version.txt").readline()


def read_requirements(file_):
    lines = []
    with open(file_) as f:
        for line in f.readlines():
            line = line.strip()
            if line.startswith('-e ') or line.startswith('http://') or line.startswith('https://'):
                lines.append(line.split('#')[1].split('egg=')[1])
            elif line.startswith('#') or line.startswith('-'):
                pass
            else:
                lines.append(line)
    return lines


setup(
    name='releasewarrior',
    version=version,
    packages=find_packages(),
    include_package_data=True,
    tests_require=read_requirements('requirements-dev.txt'),
    install_requires=read_requirements('requirements.txt'),
    entry_points="""
        [console_scripts]
        release=releasewarrior.cli:cli
    """,
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
    ],
)
