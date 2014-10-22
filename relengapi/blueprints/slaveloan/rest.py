# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import wsme.types


class Machine(wsme.types.Base):
    "Represents a single loanable Machine"

    #: Unique ID for this entry
    id = int
    #: The machines Fully Qualified Domain Name
    fqdn = unicode
    #: The machines IP Address
    ipaddr = unicode


class Human(wsme.types.Base):
    "Represents a single Human requesting a loan"

    #: Unique ID for this entry
    id = int
    #: The humans full LDAP name
    ldap = unicode
    #: The humans full bugzilla e-mail address
    bugzilla = unicode


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


class LoanRequest(wsme.types.Base):
    "Represents a new loan request"

    #: Initial Status
    status = unicode
    #: Users LDAP username
    LDAP = unicode
    #: Users Bugzilla e-mail
    bugzilla = unicode
    #: If known in advance, fqdn of the machine to loan
    fqdn = unicode
    #: If known in advance, ip address of the machine to loan
    ipaddress = unicode


MachineClassMapping = wsme.types.DictType(key_type=unicode,
                                          value_type=wsme.types.ArrayType(unicode))
