
# Installation and running

    pip install -r requirements.txt -r requirements-dev.txt -c requirements_frozen.txt 
    pip install -e . -c requirements_frozen.txt 
    Fill in `client_secrets.json.tmpl` as `client_secrets.json` for auth0 connections
    python3 shipit_signoff/__init__.py

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