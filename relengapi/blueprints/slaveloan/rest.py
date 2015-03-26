# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import wsme.types


class Machine(wsme.types.Base):
    "Represents a single loanable Machine"

    #: Unique ID for this entry
    id = int
    #: The machine's Fully Qualified Domain Name
    fqdn = unicode
    #: The machine's IP Address
    ipaddress = unicode


class Human(wsme.types.Base):
    "Represents a single Human requesting a loan"

    #: Unique ID for this entry
    id = int
    #: The human's full LDAP e-mail
    ldap_email = unicode
    #: The human's full bugzilla e-mail address
    bugzilla_email = unicode


class Loan(wsme.types.Base):
    "Represents a singe Loan Entry"

    #: Unique ID for this entry
    id = int
    #: Current status of the loan. Valid values ("PENDING", "READY")
    status = unicode
    #: Bugzilla Bug number of the Loan Request
    bug_id = int
    #: The :api:type:`Human` using this loan
    human = Human
    #: The :api:type:`Machine` assigned to this loan
    machine = Machine


class HistoryEntry(wsme.types.Base):
    "Represents a single log line of History Loan Entry"

    #: Unique ID for this line
    id = int
    #: Unique ID of the loan this log line is for
    loan_id = int
    #: Datetime string (in UTC) of this entry. (e.g. "2014-06-06T20:02:46.937065+00:00")
    timestamp = unicode
    #: The actual log message
    msg = unicode


class ManualAction(wsme.types.Base):
    "Represents a need for an admin to perform a manual action"
    #: Unique ID for this action
    id = int
    #: Unique ID of the loan this log line is for
    loan_id = int
    #: Datetime string (in UTC) of the start of action. (e.g. "2014-06-06T20:02:46.937065+00:00")
    timestamp_start = unicode
    #: Datetime string (in UTC) when action was completed. (e.g. "2014-06-06T22:02:46.937065+00:00")
    timestamp_complete = unicode
    #: Who performed the completion (admin ldap)
    complete_by = unicode
    #: What action needs performing
    msg = unicode


class UpdateManualAction(wsme.types.Base):
    "Represents payload used to update a manual action"
    #: Mark the action as complete
    complete = bool


class LoanAdminRequest(wsme.types.Base):
    "Represents a new loan request with admin details"

    #: Initial Status
    status = unicode
    #: Users full LDAP e-mail
    ldap_email = unicode
    #: Users Bugzilla e-mail
    bugzilla_mail = unicode
    #: If known in advance, fqdn of the machine to loan
    fqdn = unicode
    #: If known in advance, ip address of the machine to loan
    ipaddress = unicode


class LoanRequest(wsme.types.Base):
    "Represents a new loan request"

    #: (optional) Loan Bug Id, if not passed in we create one for you
    loan_bug_id = wsme.types.wsattr(int, mandatory=False)
    #: Users full LDAP e-mail
    ldap_email = unicode
    #: (optional) Users Bugzilla e-mail, defaults to <ldap_email> if not supplied
    bugzilla_email = wsme.types.wsattr(unicode, mandatory=False)
    #: Slave type to loan
    requested_slavetype = unicode
