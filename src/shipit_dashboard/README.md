ShipIt Dashboard Backend
========================


Initialize the project
----------------------

Add a Bug Analysis to list some bugs:

```python
from shipit_dashboard.models import BugAnalysis
from shipit_dashboard.db import db

ba = BugAnalysis('demo')
ba.parameters = "v4=affected&o5=equals&f1=cf_status_firefox50&o3=equals&v3=affected&o1=equals&j2=O    R&resolution=---&resolution=FIXED&f4=cf_status_firefox48&v5=affected&query_format=advanced&f3=cf_statu    s_firefox49&f2=OP&o4=equals&f5=cf_status_firefox47&v1=fixed&f7=CP"
db.session.add(ba)
db.session.commit()
```
