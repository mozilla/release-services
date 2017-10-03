
# Installation and running


    https://docs.mozilla-releng.net/contributing/developing.html#not-using-please-command

    pip install -r requirements.txt -r requirements-dev.txt -c requirements_frozen.txt
    pip install -e . -c requirements_frozen.txt

Set environment variables:

    * export APP_SETTINGS=$(pwd)/settings.py
    * export FLASK_APP=shipit_signoff.flask:app
    * export DATABASE_URL=postgresql://localhost:5432/
    * export APP_URL=123
    * export AUTH_CLIENT_ID=123
    * export AUTH_CLIENT_SECRET=123

Run the app:

    flask run

# Generating API documentation

    swagger-codegen generate -i api.yml -l html2


# Definining a Sign-off Step

*Currently under development, will change soon*

The policy for a sign-off step consists of two parts. The first is the method to use, such as `local` or `balrog`, and the second is the definition.


## Example 1: Locally check for two members of releng group

    {
    	"method": "local",
    	"definition": {
    		"releng": 2
    	}
    }

## Example 2: Defer to balrog

	{
		"method": "balrog",
		"definition": "Some balrog URL, or other data structure"
	}
