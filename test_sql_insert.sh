#!/bin/bash
rm -f test.db
sqlite3 -init test_sql_insert.sql test.db < /dev/null
