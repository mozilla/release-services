CREATE TABLE IF NOT EXISTS projects (
    id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY (name)
);

CREATE TABLE IF NOT EXISTS hashes (
    hg_changeset VARCHAR(40) NOT NULL,
    git_changeset VARCHAR(40) NOT NULL,
    project_id SMALLINT UNSIGNED NOT NULL,
    date_added int UNSIGNED NOT NULL,
    INDEX (hg_changeset),
    INDEX (git_changeset),
    INDEX (project_id),
    INDEX (project_id, date_added),
    UNIQUE INDEX (hg_changeset, project_id),
    UNIQUE INDEX (git_changeset, project_id)
);
