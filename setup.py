from setuptools import setup
import os
import re

def find_version():
    with open('gui/tasmotizer.py', 'r') as version_file:
        version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                                  version_file.read(), re.M)
        if version_match:
            return version_match.group(1)
        raise RuntimeError(_("Unable to find version string."))

if os.name == "nt":
    scripts = None
    entry_points = {
        {
        'console_scripts': ['tasmotizer=tasmotizer:main'],
        }
    }
else:
    scripts = ['tasmotizer.py']
    entry_points = None

setup(
    name='tasmotizer',
    version=find_version(),
    url='https://github.com/tasmota/tasmotizer',
    py_modules=['tasmotizer', 'utils'],
    packages=['esptool', 'gui'],
    license='GPLv3',
    author='jziolkowski',
    author_email='jacek@ziolkowscy.com',
    description=_('The time has come to... Tasmotize!'),
    long_description=_("Tasmotizer is a dedicated flashing tool for <a href=https://github.com/arendst/Tasmota>Tasmota</>, featuring automatic firmware backup, downlading release and development bins, and device configuration."),
    python_requires='>=3.6',
    install_requires=[
        "pyserial>=3.0",
        "PyQt5>=5.10"
    ],
    entry_points=entry_points,
    scripts=scripts,
    classifiers=[
        _("Programming Language :: Python :: 3"),
        _("License :: OSI Approved :: GNU General Public License v3 (GPLv3)"),
        _("Operating System :: OS Independent"),
    ],
    project_urls={
        _("Issue Tracker"): "https://github.com/tasmota/tasmotizer/issues",
        _("Documentation"): "https://github.com/tasmota/tasmotizer/wiki"),
    },
)
