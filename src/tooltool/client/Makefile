check: python-tests shell-tests tox

shell-tests:
	sh test.sh

python-tests: 
	clear
	python test_tooltool.py

python-test-%:
	clear
	python test_tooltool.py $*

tox:
	tox

.PHONY: check clean shell-tests python-tests python-tests-% tox
