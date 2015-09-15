import setuptools


setuptools.setup(
    name='gerrit-logger',
    version='1.0.0',
    description='Log the Gerrit event stream in markdown.',
    author='Dolph Mathews',
    author_email='dolph.mathews@gmail.com',
    url='http://github.com/dolph/gerrit-logger',
    scripts=['event_logger.py', 'events_in_english.py'],
    install_requires=['paramiko', 'dogpile.cache'],
    py_modules=['gerrit_growler'],
    entry_points={
        'console_scripts': [
            'gerrit-logger = event_logger:main',
            'gerrit-events-in-english = events_in_english:main']},
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Topic :: Utilities',
    ],
)
