

    pip install -r requirements.txt
    cd shipit_signoff
    swagger-codegen generate -i api.yml -l python-flask 
    cd ..
    ./runme.sh
