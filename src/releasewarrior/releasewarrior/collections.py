import collections

Release = collections.namedtuple('Release', 'product, version, branch')
PrerequisiteTask = collections.namedtuple('PrerequisiteTask', 'bug, deadline, description, resolved')
InflightTask = collections.namedtuple('InflightTask', 'position, description, docs, resolved')
Issue = collections.namedtuple('Issue', 'who, bug, description, resolved, future_threat')
