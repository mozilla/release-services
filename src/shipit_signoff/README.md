

    pip install -r requirements.txt
    cd shipit_signoff
    cd ..
    ./runme.sh

To generate documentation:
    swagger-codegen generate -i api.yml -l html2
