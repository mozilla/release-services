# generated using pypi2nix tool (version: 1.5.0.dev0)
#
# COMMAND:
#   pypi2nix --basename mysql2pgsql -V 2.7 -e py-mysql2pgsql -E postgresql mysql.lib -v
#

{ pkgs, python, commonBuildInputs ? [], commonDoCheck ? false }:

self: {

  "MySQL-python" = python.mkDerivation {
    name = "MySQL-python-1.2.5";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/a5/e9/51b544da85a36a68debe7a7091f068d802fc515a3a202652828c73453cad/MySQL-python-1.2.5.zip";
      sha256 = "811040b647e5d5686f84db415efd697e6250008b112b6909ba77ac059e140c74";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [ ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.gpl1;
      description = "Python interface to MySQL";
    };
  };



  "PyYAML" = python.mkDerivation {
    name = "PyYAML-3.11";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/75/5e/b84feba55e20f8da46ead76f14a3943c8cb722d40360702b2365b91dec00/PyYAML-3.11.tar.gz";
      sha256 = "c36c938a872e5ff494938b33b14aaa156cb439ec67548fcab3535bb78b0846e8";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [ ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.mit;
      description = "YAML parser and emitter for Python";
    };
  };



  "argparse" = python.mkDerivation {
    name = "argparse-1.4.0";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/18/dd/e617cfc3f6210ae183374cd9f6a26b20514bbb5a792af97949c5aacddf0f/argparse-1.4.0.tar.gz";
      sha256 = "62b089a55be1d8949cd2bc7e0df0bddb9e028faefc8c32038cc84862aefdd6e4";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [ ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.psfl;
      description = "Python command-line parsing library";
    };
  };



  "psycopg2" = python.mkDerivation {
    name = "psycopg2-2.6.2";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/7b/a8/dc2d50a6f37c157459cd18bab381c8e6134b9381b50fbe969997b2ae7dbc/psycopg2-2.6.2.tar.gz";
      sha256 = "70490e12ed9c5c818ecd85d185d363335cc8a8cbf7212e3c185431c79ff8c05c";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [ ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.lgpl2;
      description = "psycopg2 - Python-PostgreSQL Database Adapter";
    };
  };



  "py-mysql2pgsql" = python.mkDerivation {
    name = "py-mysql2pgsql-0.1.5";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/28/49/c82e4313c63b26224950bef47ab19f52a921dd4c279abf31aa3ee9d9cbbe/py-mysql2pgsql-0.1.5.tar.gz";
      sha256 = "024d3f1d3994679421102a2cb70c1fde1306bdf8c70839db907a728324c65cdf";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [
      self."MySQL-python"
      self."PyYAML"
      self."argparse"
      self."psycopg2"
      self."termcolor"
    ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.mit;
      description = "Tool for migrating/converting from mysql to postgresql.";
    };
  };



  "termcolor" = python.mkDerivation {
    name = "termcolor-1.1.0";
    src = pkgs.fetchurl {
      url = "https://pypi.python.org/packages/8a/48/a76be51647d0eb9f10e2a4511bf3ffb8cc1e6b14e9e4fab46173aa79f981/termcolor-1.1.0.tar.gz";
      sha256 = "1d6d69ce66211143803fbc56652b41d73b4a400a2891d7bf7a1cdf4c02de613b";
    };
    doCheck = commonDoCheck;
    buildInputs = commonBuildInputs;
    propagatedBuildInputs = [ ];
    meta = with pkgs.stdenv.lib; {
      homepage = "";
      license = licenses.mit;
      description = "ANSII Color formatting for output in terminal.";
    };
  };

}