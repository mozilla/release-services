{ releng_pkgs }:

let
  inherit (releng_pkgs.pkgs) writeScriptBin bash openssl coreutils;
in writeScriptBin "createcert" ''
  #!${bash}/bin/bash

  DIR=$1

  if [[ -z "$DIR" ]]; then
    ${coreutils}/bin/echo "You need to provide directory where to create certificates."
    exit 1
  fi

  if [[ ! -d "$DIR" ]]; then
    ${coreutils}/bin/echo "Directory '$DIR' does not exists."
    exit 1
  fi

  CA_KEY="$DIR/ca.key"
  CA_CERT="$DIR/ca.crt"

  if [[ -f $CA_KEY ]] ; then
    ${coreutils}/bin/echo "Ca already exists. Please remove it before using this script."
    exit 1
  fi

  function build_ca {
    # Build root key
    ${openssl.bin}/bin/openssl genrsa -out $CA_KEY 2048
    ${coreutils}/bin/echo "Built root key"

    # Self sign ca
    ${openssl.bin}/bin/openssl req -x509 -new -nodes -key $CA_KEY -days 1024 -out $CA_CERT -subj "/C=FR/ST=France/L=Paris/O=Mozilla/OU=Dev/CN=RelengAPI"
    ${coreutils}/bin/echo "Built root CA"
  }

  function build_child {
    NAME=$1
    if [[ ! $NAME ]] ; then
      ${coreutils}/bin/echo "Specify a pkey/cert name"
      exit 1
    fi

    KEY="$DIR/$NAME.key"
    CERT="$DIR/$NAME.crt"
    CSR="$DIR/$NAME.csr"

    # Build a private key
    ${openssl.bin}/bin/openssl genrsa -out $KEY 2048

    # Build csr with mandatory subjectAltName
    ${openssl.bin}/bin/openssl req -sha256 -new -key $KEY -out $CSR \
      -subj "/C=FR/ST=France/L=Paris/O=Mozilla/OU=Dev/CN=localhost" \
      -reqexts SAN \
      -config <(cat ${openssl.out}/etc/ssl/openssl.cnf \
        <(printf "[SAN]\nsubjectAltName=DNS:localhost,DNS:127.0.0.1"))

    # Sign with CA
    ${openssl.bin}/bin/openssl x509 -req -in $CSR \
      -CA $CA_CERT -CAkey $CA_KEY -CAcreateserial -out $CERT -days 500 \
      -extensions SAN \
      -extfile <(cat ${openssl.out}/etc/ssl/openssl.cnf \
        <(printf "[SAN]\nsubjectAltName=DNS:localhost,DNS:127.0.0.1"))

    # Cleanup csr
    ${coreutils}/bin/rm $CSR

    # Hash cert directory
    ${openssl.bin}/bin/c_rehash $DIR
  }

  build_ca
  build_child server
''
