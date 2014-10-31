import wsme.types

class MapFile(wsme.types.Base):
    "Plain text containing git to hg sha mappings, one per line (git_commit hg_changeset\\n)"
