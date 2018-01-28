from setuptools import setup

setup(name='jplankton.project-manager.shunt',
      version='0.1',
      description='Materialize a set of Jinja2 template files to "shunt" a project into place as a starting point',
      classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6',
      ],
      url='https://github.com/velezj/project-manager',
      author='Javier Velez',
      author_email='javier@salientlore.ml',
      license='MIT',
      packages=['shunt'],
      scripts=['bin/jplankton.project-manager.shunt'],
      install_requires=[
          "jinja2",
          "pyyaml",
      ],
      include_package_data=True,
      zip_safe=False)
