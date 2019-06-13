from setuptools import setup

setup(name='symdim',
      version='0.1',
      description='An algebraic manipulation and dimensional analysis tool using SymPy and Astropy.units',
      url='http://github.com/AndrewChap/symdim',
      author='Andrew Chap',
      author_email='andrew@andrewchap.com',
      license='MIT',
      packages=['symdim'],
      install_requires=[
          'num2tex',
          'sympy',
          'astropy',
      ],
      zip_safe=False,
      )
