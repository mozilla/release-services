check:
	python test_lookaside.py

check-%:
	clear
	python test_lookaside.py $*

.PHONY: check-% check-all
