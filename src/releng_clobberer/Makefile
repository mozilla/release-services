mysql_dump: require-DB_PASSWORD
	@rm -f mysqldump_clobberer.sql
	@echo "DROP TABLE IF EXISTS releng_clobberer_builds;" > mysqldump_clobberer.sql
	@echo "DROP TABLE IF EXISTS releng_clobberer_times;" >> mysqldump_clobberer.sql
	@ssh $(USER)@relengwebadm.private.scl3.mozilla.com \
		"mysqldump opt -u clobberer2 -p$(DB_PASSWORD) -h devtools-rw-vip.db.scl3.mozilla.com clobberer" \
		>> mysqldump_clobberer.sql 2> /dev/null
	@echo "RENAME TABLE builds TO releng_clobberer_builds;" >> mysqldump_clobberer.sql
	@echo "RENAME TABLE clober_times TO releng_clobberer_times;" >> mysqldump_clobberer.sql
	@echo "Production database dumped into: mysqldump_clobberer.sql"


sqlite_load:
	cat mysqldump_clobberer.sql | sqlite3 ../../app.db


require-DB_PASSWORD:
	@if [[ -z "$$DB_PASSWORD" ]]; then \
		echo ""; \
		echo "You need to specify DB_PASSWORD variable that, allows you to connect to mysql databaseeg."; \
		echo ""; \
		exit 1; \
	fi
