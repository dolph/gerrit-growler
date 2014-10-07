import setuptools


setuptools.setup(
    name='gerrit-growler',
    version='1.0.0',
    description='Receive growl notifications from Gerrit.',
    author='Dolph Mathews',
    author_email='dolph.mathews@gmail.com',
    url='http://github.com/dolph/gerrit-growler',
    scripts=['gerrit_growler.py'],
    install_requires=['paramiko', 'dogpile.cache'],
    py_modules=['gerrit_growler'],
    entry_points={'console_scripts': ['gerrit-growler = gerrit_growler:main']},
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Topic :: Utilities',
    ],
)
