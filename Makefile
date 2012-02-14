check: python-tests

python-tests: 
	clear
	python test_tooltool.py

python-test-%:
	clear
	python test_tooltool.py $*

.PHONY: check sh-tests python-tests python-tests-%
