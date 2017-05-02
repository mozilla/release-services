ShipIt Dashboard Backend
========================


Initialize the project
----------------------

Add a Bug Analysis to list some bugs:

```python
from shipit_uplift.models import BugAnalysis
from shipit_uplift.flask import db

requests = {
    'aurora' : 'o5=substring&j9=OR&list_id=13189500&o2=substring&f12=CP&o4=substring&known_name=approval-mozilla-aurora&f10=requestees.login_name&f1=OP&o3=substring&f0=OP&f8=OP&v3=approval-mozilla-aurora%3F&columnlist=product%2Ccomponent%2Clast_visit_ts%2Cassigned_to%2Cbug_status%2Cresolution%2Cshort_desc%2Cchangeddate&query_based_on=approval-mozilla-aurora&f9=OP&f4=flagtypes.name&query_format=advanced&o10=substring&j1=OR&f3=flagtypes.name&f2=flagtypes.name&f11=CP&f5=flagtypes.name&f6=CP&f7=CP',
    'beta' : 'o5=substring&f10=requestees.login_name&f1=OP&j9=OR&o3=substring&list_id=13189499&f0=OP&f8=OP&v3=approval-mozilla-beta%3F&columnlist=product%2Ccomponent%2Clast_visit_ts%2Cassigned_to%2Cbug_status%2Cresolution%2Cshort_desc%2Cchangeddate%2Ccf_tracking_firefox38&query_based_on=approval-mozilla-beta&o2=substring&f9=OP&f4=flagtypes.name&query_format=advanced&o10=substring&f12=CP&j1=OR&f3=flagtypes.name&f2=flagtypes.name&o4=substring&f11=CP&f5=flagtypes.name&f6=CP&f7=CP&known_name=approval-mozilla-beta',
    'release' : 'o5=substring&j9=OR&list_id=13189498&o2=substring&f12=CP&o4=substring&known_name=approval-mozilla-release&f10=requestees.login_name&f1=OP&o3=substring&f0=OP&f8=OP&v3=approval-mozilla-release%3F&query_based_on=approval-mozilla-release&f9=OP&f4=flagtypes.name&query_format=advanced&o10=substring&j1=OR&f3=flagtypes.name&f2=flagtypes.name&f11=CP&f5=flagtypes.name&f6=CP&f7=CP',
    'esr45' : 'o5=substring&f10=requestees.login_name&f1=OP&j9=OR&o3=substring&list_id=13189501&f0=OP&f8=OP&v3=approval-mozilla-esr45%3F&query_based_on=approval-esr45&o2=substring&f9=OP&f4=flagtypes.name&query_format=advanced&o10=substring&f12=CP&j1=OR&f3=flagtypes.name&f2=flagtypes.name&o4=substring&f11=CP&f5=flagtypes.name&f6=CP&f7=CP&known_name=approval-esr45',
}

for name, parameters in requests.items():
    ba = BugAnalysis(name)
    ba.parameters = parameters
    db.db.session.add(ba)

db.db.session.commit()
```
