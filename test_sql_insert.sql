CREATE TABLE hashes (
	hg_changeset VARCHAR(40) NOT NULL, 
	git_commit VARCHAR(40) NOT NULL, 
	project_id INTEGER NOT NULL, 
	date_added INTEGER NOT NULL, 
	FOREIGN KEY(project_id) REFERENCES projects (id)
);
CREATE TABLE projects (
	id INTEGER NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);
CREATE INDEX git_commit ON hashes (git_commit);
CREATE INDEX hg_changeset ON hashes (hg_changeset);
CREATE INDEX project_id ON hashes (project_id);
CREATE INDEX project_id__date_added ON hashes (project_id, date_added);
CREATE UNIQUE INDEX project_id__git_commit ON hashes (project_id, git_commit);
CREATE UNIQUE INDEX project_id__hg_changeset ON hashes (project_id, hg_changeset);

        insert into hashes (project_id, hg_changeset, git_commit, date_added) values
          (1, '111111705d7c41c8f101b5b1e3438d95d0fcfa7a', 'a7afcf0d59d8343e1b5b101f8c14c7d507111111', 12345.0),
          (1, '222222705d7c41c8f101b5b1e3438d95d0fcfa7a', 'a7afcf0d59d8343e1b5b101f8c14c7d507222222', 12346.0),
          (1, '333333333d7c41c8f101b5b1e3438d95d0fcfa7a', 'a7afcf0d59d8343e1b5b101f8c14c7d333333333', 12347.0)
    ;
select * from hashes;
