ShipIt
======


current implementation
----------------------

- 2 parts webfrontend and releaserunner
- webfrontend is used to
  - accepts release data and stores it in the database
  - start a release
  - be the source of truth for other services
  - does all the sanity checks before the release
- releaserunner
  - talks to webfrontend to get releases ready to go
  - creates the tc graph (tasks are signed)
  - starts a release process
  - marks the release in shipit to "started"
- readonly endpoints (used by other services)
  - TODO: list them
- there is a cronjob somewhere, generating https://product-details.mozilla.org/



- multiple release products
  - Firefox (7-8days)
  - Firefox Beta (1-2day)
  - Fennex
  - Fennex Beta
  - Thunderbird??
    

Technical stuff:
 - relengapi stack
 - relengapi repo
