import os
import sys
from setuptools import setup

def _read(fn):
    path = os.path.join(os.path.dirname(__file__), fn)
    return open(path).read()

setup(name='inventor',
      version='1.0-pre-alpha.1',
      description='Product inventory system.',
      author='Steinthor Palsson',
      author_email='steini90@gmail.com',
      url='',
      license='MIT',
      platforms='ALL',
      include_package_data=True, # Install plugin resources.

      packages=[
        'inventor',
      ],
      

      install_requires=[
          'psycopg2',
          'flask',
          'flask-restful',
      ]
      + (['ordereddict'] if sys.version_info < (2, 7, 0) else []),
      ),

