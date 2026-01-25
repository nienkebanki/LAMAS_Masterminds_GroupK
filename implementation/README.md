# Masterminds


Running  `masterminds.py` requires the following:
    - more_itertools
    - installing the version of mlsolver included in this repository using `python setup.py install` inside the `mlsolver` folder.

`masterminds.py` will plot the leakage over rounds of the information and the average number of rounds necesarry for a win.

`mlsolver` is taken from https://github.com/erohkohl/mlsolver. We have modified the solve function in `kripke.py` to have public announcement functionality only. Everything else is taken verbatim from erohkol/mlsolver.