CREATE TABLE IF NOT EXISTS projects (
   id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
   name VARCHAR(255) NOT NULL,
   PRIMARY KEY (id),
   UNIQUE KEY (name)
);

CREATE TABLE IF NOT EXISTS hashes (
   id INT UNSIGNED NOT NULL AUTO_INCREMENT,
   hg_changeset VARCHAR(40) NOT NULL,
   git_changeset VARCHAR(40) NOT NULL,

   PRIMARY KEY (id),
   UNIQUE INDEX (hg_changeset),
   UNIQUE INDEX (git_changeset)
);

CREATE TABLE IF NOT EXISTS projects_to_hashes (
    project_id INT UNSIGNED NOT NULL,
    hash_id INT UNSIGNED NOT NULL,
    date_added DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    KEY (project_id),
    KEY (hash_id),
    KEY (date_added)
);
