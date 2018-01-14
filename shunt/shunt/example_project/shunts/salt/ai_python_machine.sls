ai-python-machine.system-packages:
  pkg.installed:
    - pkgs:
        - python3
        - python3-pip
        - python-pip # for the pip state below :(
        - emacs-nox
        
ai-python-machine.pip-packages:
  pip.installed:
    - pkgs:
        - pipenv
        - numpy
        - scipy
        - sklearn
        - matplotlib
        - pandas
        - bunch
        - nltk
    - require:
        - pkg: ai-python-machine.system-packages
