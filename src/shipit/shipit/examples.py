import json
import datetime
from functools import wraps


# workflow.json
# {
#     "state1": {
#         transitions: [
#             "https://.../check-rev"
#         ]
#     }
# }

release = Process.create('schemas/workflow_firefox_beta.json')
release.config
# {
#     "ticks": [
#       {"state": "state1", "timestamp": 1234, "counter": 1}
#     ],
#     "states": [
#        {
#         "name": "state1",
#         "transition": {
#           "url": "http://...",
#           "callback_url": "https://...."
#           "config": {}
#         },
#         "status": "ready/error/running/success",
#        },
#        {
#          "name": state2",
#        }
#     ]
# }

assert release == Process(release.config)


class State:

    def status(self):
        # running
        # success
        # error

input_data = State("input_data")


release.pipeline = [
    input_data
    "check_rev"
    ...
]

release.current_state = input_data
release.tick(input)


release.current_state = "check_rev"
release.tick({}) # /release/<uid>/tick

@transition(....)
def input_firefox_release_data(input_):
    signing_releng = Process.create(input_.something)
    signing_qa = Process.create(input_.somethin2)

    if signing_releng.done and signing_qa.done:
        return Success(
        )
    return Error(
        signing_releng.error
        signing_qa.error
    )





class Success:
    pass


class Error:
    pass


class ValidationError(RuntimeError):
    pass


def validate(*args):
    pass


def check(*args):
    pass


def transition(input_schema, success_schema, error_schema):
    def wrapper(func):
        @wraps(func)
        def inner(input_):
            try:
                validate(input_schema, input_)
            except ValidationError as e:
                pass
            result = func(input_)
            if isinstance(result, Success):
                return validate(success_schema, result)
            elif isinstance(result, Error):
                return validate(error_schema, result)
            else:
                raise RuntimeError('ouch!')
        return inner
    return wrapper


# /check-rev/<hash>
# /check-rev/latest
@app.route("/check-revs")
@transition('schemas/input.json',
            success='schemas/output.json',
            error='schemas/error.json')
Sdef check_for_existing_revision(input_):
    success = check(input_['rev'], input_['repo'])

    if success
        return Success(
            rev=input_['rev'],
            repo=input_['repo'],
            exists=datetime.datetime.now(),
        )

    return Error(
        input=input_,
        message="Bakjshd ajkhd "
    )

# Expected output
"""
{
    "product": "firefox",
    "version": "48.0.1",
    "build_number": 5,
    "revision": "abcdeds",
    "repo": "https://hg.mozilla.org/releases/mozilla-release",
    "locales": {
        "af": "abcdef",
        "de": "axxfasd",
    },
    "gpg_pub_key": "data",
}
"""


# after stage0
"""
{
   stage0: {
    "product": "firefox",
    "repository_url": "https://hg.mozilla.org/releases/mozilla-release",
    "timestamps": [
        ( "start", "2016-07-29...", "a message" )
    ]
   }
}
"""

# after stage1
"""
{
   stage0: {
     "product": "firefox",
     "product_repository_url": "https://hg.mozilla.org/releases/mozilla-release",
     "timestamps": [
       ( "start", "2016-07-29...", "a message" ),
       ( "end", "2016-07-29...", "a message" )
     ]
   },
   stage1: {
     "product_revision": "135457abd",
     "locales": {
       "af": "abcdef",
       "de": "axxfasd",
     }
   }
}
"""

# after stage2
"""
{
   stage0: {
     "product": "firefox",
     "product_repository_url": "https://hg.mozilla.org/releases/mozilla-release",
     "timestamps": [
       ( "start", "2016-07-29...", "a message" ),
       ( "end", "2016-07-29...", "a message" )
     ]
   },
   stage1: {
     "product_revision": "135457abd",
     "locales": {
       "af": "abcdef",
       "de": "axxfasd",
     }
   },
   stage2: {
     "product_revision_status": 200,
     "locales_status": {
       "af": 200,
       "de": 404,
     }
   },
   # use TC Hooks? the task should call the corresponding URL when done with the status. Kill the hook after.
   stage3: {
     "en-US_bianry_status":
        {"linux": 200,
         "linux64": 404,
         "win32": 404,
         ...
        }
   }
}
"""


"""
terminology
- unidirectional workflow
- uniflow

- train
- trainstop
- traincargo

"""


"""
TODO:

- working together on the first task
    using tests to input data.

- another 2 tasks separatly
"""

