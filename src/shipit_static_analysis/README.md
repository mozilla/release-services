Static Analysis
===============

Configuration
-------------

As every other services in `mozilla-releng/services`, the static analysis bot is configured through the [Taskcluster secrets service](https://tools.taskcluster.net/secrets)

The following configuration variables are currently supported:

* `APP_CHANNEL` **[required]** is provided by the common configuration (staging or production)
* `REPORTERS` **[required]** lists all the reporting tools to use when a static analysis is completed (details below)
* `CLANG_FORMAT_ENABLED` is a boolean controlling if `clang-format` should be run on the patches (enabled by default)
* `PAPERTRAIL_HOST` is the optional Papertrail host configuration, used for logging.
* `PAPERTRAIL_PORT` is the optional Papertrail port configuration, used for logging.
* `SENTRY_DSN` is the optional Sentry full url to report runtime errors.
* `MOZDEF` is the optional MozDef log destination.

The `REPORTERS` configuratin is a list of dictionaries describing which reporting tool to use at the end of the patches static analysis.
Supported reporting tools are emails (for admins), MozReview and Phabricator.

Each reporter configuration must contain a `reporter` key with a unique name per tool. Each tool has its own configuration requirement.

Reporter: Mail
--------------

Key `reporter` is `mail`

The emails are sent through Taskcluster notify service, the hook must have `notify:email:*` in its scopes (enabled on our staging & production instances)

Only one configuration is required: `emails` is a list of emails addresses receiving the admin output for each analysis.

Reporter: MozReview
-------------------

Key `reporter` is `mozreview`

Configuration:

 * `url` : The Mozreview api url
 * `username` : The Mozreview account's username
 * `api_key` : The Mozreview account's api key 
 * `style` : Comment style to use, `clang-tidy` only reports issues found with this tool, `full` reports all errors found.
 * `publish_success` : a boolean describing if a successfull analysis must be reported (disabled by default)


Reporter: Phabricator
---------------------

Key `reporter` is `phabricator`

Configuration:

 * `url` : The Phabricator api url
 * `api_key` : The Phabricator account's api key 

Example configuration
---------------------

```json
{
  "common": {
    "APP_CHANNEL": "staging",
    "PAPERTRAIL_HOST": "XXXX.papertrail.net",
    "PAPERTRAIL_PORT": 12345
  },
  "shipit-static-analysis": {
    "REPORTERS": [
      {
        "reporter": "mail",
        "emails": [
          "xxx@mozilla.com",
          "yyy@mozilla.com"
        ]
      },
      {
        "reporter": "phabricator",
        "url": "https://dev.phabricator.mozilla.com",
        "api_key": "deadbeef123456"
      },
      {
        "reporter": "mozreview",
        "url": "https://reviewboard.mozilla.org",
        "api_key": "coffee123456",
        "username": "sa-bot-staging",
        "style": "full"
      }
    ]
  }
}
```
