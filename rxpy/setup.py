from distutils.core import setup

setup(name='RXPY',
      version='0.0.0',
      description='A Regular Expression Library for Python',
      long_description='''
RXPY is a regular expression library, written purely in Python, that is almost
completely backwards compatible with the standard Python re library (only
locale-based character groups are not supported).

It has a modular design that allows different alphabets and engines to be
used.  This allows regular expressions to be defined over sequences of
arbitrary objects (a mapping between objects and the characters used in the
regular expression must exist; this is defined by the alphabet).

The initial engine is a simple recursive descent implementation, but future
releases will support a DFA-based solution similar to re2.
''',
      author='Andrew Cooke',
      author_email='andrew@acooke.org',
      url='http://www.acooke.org/rxpy/',
      packages=['rxpy',
                'rxpy.alphabet', 'rxpy.alphabet._test',
                'rxpy.direct',   'rxpy.direct._test',
                'rxpy.parser',   'rxpy.parser._test',
                ],
      package_dir = {'':'src'},
      keywords = "regular expression",
      classifiers=['Development Status :: 3 - Alpha',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
                   'License :: OSI Approved :: Mozilla Public License 1.1 (MPL 1.1)',
                   'Natural Language :: English',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python :: 2.7',
                   'Programming Language :: Python :: 2.6',
                   'Topic :: Software Development',
                   'Topic :: Software Development :: Libraries',
                   'Topic :: Software Development :: Libraries :: Python Modules',
                   'Topic :: Text Processing',
                   'Topic :: Text Processing :: Filters',
                   'Topic :: Text Processing :: General',
                   'Topic :: Utilities'
                   ]
     )
