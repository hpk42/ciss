import os, sys
if sys.version_info >= (3,0):
    from distribute_setup import use_setuptools
    use_setuptools()
from setuptools import setup

long_description = """
ciss: code-centered single-file "ISSUES.txt" issue tracking
Platforms: Linux, Win32, OSX
Interpreters: Python versions 2.4 through to 3.1, Jython 2.5.1. 
(c) Holger Krekel 2009
"""
from ciss import __version__ as version
def main():
    setup(
        name='ciss',
        description='ciss: code-centered single "ISSUES.txt" issue tracking',
        long_description = long_description,
        version=version,
        url='http://codespeak.net/ciss',
        license='MIT license',
        platforms=['unix', 'linux', 'osx', 'cygwin', 'win32'],
        author='holger krekel',
        author_email='holger at merlinux.eu',
        entry_points={'console_scripts': [
            'ciss = ciss:main',
        ]},
        classifiers=['Development Status :: 3 - Alpha',
                     'Intended Audience :: Developers',
                     'License :: OSI Approved :: MIT License',
                     'Operating System :: POSIX',
                     'Operating System :: Microsoft :: Windows',
                     'Operating System :: MacOS :: MacOS X',
                     'Topic :: Utilities',
                     'Intended Audience :: Developers',
                     'Programming Language :: Python'],
        py_modules = ['ciss'],
        install_requires = ['py'],
        zip_safe=False,
    )

if __name__ == '__main__':
    main()

