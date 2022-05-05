
import glob
import os
import sys

from setuptools import find_packages, setup

# read the contents of your README file
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    LONG = f.read()

conf = []
templates = []

for name in glob.glob('config/plugins.d/*.conf'):
    conf.insert(1, name)

for name in glob.glob('kc/cli/templates/*.mustache'):
    templates.insert(1, name)

if os.geteuid() == 0:
    if not os.path.exists('/var/log/kc/'):
        os.makedirs('/var/log/kc/')

    if not os.path.exists('/var/lib/kc/tmp/'):
        os.makedirs('/var/lib/kc/tmp/')

setup(name='keepcloud',
      version='1.0.0',
      description='An essential toolset that eases server administration',
      long_description=LONG,
      long_description_content_type='text/markdown',
      classifiers=[
          "Programming Language :: Python :: 3",
          "License :: OSI Approved :: MIT License",
          "Operating System :: OS Independent",
          "Development Status :: 5 - Production/Stable",
          "Environment :: Console",
          "Natural Language :: English",
          "Topic :: System :: Systems Administration",
      ],
      keywords='nginx automation wordpress deployment CLI',
      author='Keepcloud',
      author_email='contact@keepcloud.io',
      url='https://github.com/Keepcloud/kc',
      license='MIT',
      project_urls={
          'Documentation': 'https://keepcloud.io',
          'Forum': 'https://keepcloud.io',
          'Source': 'https://github.com/Keepcloud/kc',
          'Tracker': 'https://github.com/Keepcloud/kc/issues',
      },
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests',
                                      'templates']),
      include_package_data=True,
      zip_safe=False,
      test_suite='nose.collector',
      python_requires='>=3.4',
      install_requires=[
          # Required to build documentation
          # "Sphinx >= 1.0",
          # Required to function
          'cement == 2.10.12',
          'pystache >= 0.5.4',
          'pynginxconfig >= 0.3.4',
          'PyMySQL >= 0.10.1',
          'psutil >= 5.7.3',
          'sh >= 1.14.1',
          'SQLAlchemy >= 1.3.20',
          'requests >= 2.24.0',
          'distro >= 1.5.0',
          'argcomplete >= 1.12.0',
          'colorlog >= 4.6.2',
      ],
      extras_require={  # Optional
          'testing': ['nose', 'coverage'],
      },
      data_files=[('/etc/kc', ['config/kc.conf']),
                  ('/etc/kc/plugins.d', conf),
                  ('/usr/lib/kc/templates', templates),
                  ('/etc/bash_completion.d/',
                   ['config/bash_completion.d/kc_auto.rc']),
                  ('/usr/share/man/man8/', ['docs/kc.8'])],
      setup_requires=[],
      entry_points="""
          [console_scripts]
          kc = kc.cli.main:main
      """,
      namespace_packages=[],
      )
