yapf --i --recursive ./src
yapf --i --recursive ./tests
flake8 ./src
flake8 ./tests
