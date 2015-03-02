check: python-tests shell-tests

shell-tests:
	sh test.sh

python-tests: 
	clear
	python test_tooltool.py

python-test-%:
	clear
	python test_tooltool.py $*

.PHONY: check shell-tests python-tests python-tests-%
