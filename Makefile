check:
	clear
	python test_tooltool.py

check-%:
	clear
	python test_tooltool.py $*

.PHONY: check-% check-all
