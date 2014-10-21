# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import wsme.types


class Machine(wsme.types.Base):
    "Represents a single loanable Machine"
    id = int  #: Unique ID for this entry
    fqdn = unicode  #: The machines Fully Qualified Domain Name
    ipaddr = unicode  #: The machines IP Address


class Human(wsme.types.Base):
    "Represents a single Human requesting a loan"
    id = int  #: Unique ID for this entry
    ldap = unicode  #: The humans full LDAP name
    bugzilla = unicode  #: The humans full bugzilla e-mail address


class Loan(wsme.types.Base):
    "Represents a singe Loan Entry"
    id = int  #: Unique ID for this entry
    status = unicode  #: Current status of the loan. Valid values ("PENDING", "READY")
    bug_id = int  #: Bugzilla Bug number of the Loan Request
    human = Human  #: The :api:type:`Human` using this loan
    machine = Machine  #: The :api:type:`Machine` assigned to this loan


class HistoryEntry(wsme.types.Base):
    "Represents a single log line of History Loan Entry"
    id = int  #: Unique ID for this line
    loan_id = int  #: Unique ID of the loan this log line is for
    timestamp = unicode  #: Datetime string (in UTC) of this entry. (e.g. "2014-06-06T20:02:46.937065+00:00" )
    msg = unicode  #: The actual log message


class LoanRequest(wsme.types.Base):
    "Represents a new loan request"
    status = unicode  #: Initial Status
    LDAP = unicode  #: Users LDAP username
    bugzilla = unicode  #: Users Bugzilla e-mail
    fqdn = unicode  #: If known in advance, fqdn of the machine to loan
    ipaddress = unicode  #: If known in advance, ip address of the machine to loan


MachineClassMapping = wsme.types.DictType(key_type=unicode,
                                          value_type=wsme.types.ArrayType(unicode))
