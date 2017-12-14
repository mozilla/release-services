{ pkgs, python }:

let

  inherit (pkgs.lib) fileContents;

  skipOverrides = overrides: self: super:
    let
      overridesNames = builtins.attrNames overrides;
      superNames = builtins.attrNames super;
    in
      builtins.listToAttrs
        (builtins.map
          (name: { inherit name;
                   value = python.overrideDerivation super."${name}" (overrides."${name}" self);
                 }
          )
          (builtins.filter
            (name: builtins.elem name superNames)
            overridesNames
          )
        );

in skipOverrides {

  "mozilla-backend-common" = self: old: {
    name = "mozilla-backend-common-${fileContents ./../lib/backend_common/VERSION}";

    doCheck = true;

    buildInputs =[
      self."Flask-Cache"
      self."Flask-Cors"
      self."Flask-Login"
      self."Flask-Migrate"
      self."Flask-SQLAlchemy"
      self."Jinja2"
      self."connexion"
      self."flake8"
      self."flake8-coding"
      self."flake8-quotes"
      self."flask-oidc"
      self."flask-talisman"
      self."inotify"
      self."kombu"
      self."pdbpp"
      self."pytest"
      self."responses"
      self."taskcluster"
    ];

    patchPhase = ''
      # replace synlink with real file
      rm -f setup.cfg
      ln -s ${./setup.cfg} setup.cfg

      # generate MANIFEST.in to make sure every file is included
      rm -f MANIFEST.in
      cat > MANIFEST.in <<EOF
      recursive-include backend_common/*

      include VERSION
      include backend_common/VERSION
      include backend_common/*.ini
      include backend_common/*.json
      include backend_common/*.mako
      include backend_common/*.yml

      recursive-exclude * __pycache__
      recursive-exclude * *.py[co]
      EOF
    '';

    preConfigure = ''
      rm -rf build *.egg-info
    '';

    checkPhase = ''
      export LANG=en_US.UTF-8
      export LOCALE_ARCHIVE=${pkgs.glibcLocales}/lib/locale/locale-archive

      echo "################################################################"
      echo "## flake8 ######################################################"
      echo "################################################################"
      flake8 -v
      echo "################################################################"

      echo "################################################################"
      echo "## pytest ######################################################"
      echo "################################################################"
      pytest tests/ -vvv -s
      echo "################################################################"
    '';
  };

  "mozilla-cli-common" = self: old: {
    name = "mozilla-cli-common-${fileContents ./../lib/cli_common/VERSION}";

    doCheck = true;

    buildInputs =
      [ self."flake8"
        self."pytest"
      ];

    patchPhase = ''
      # replace synlink with real file
      rm -f setup.cfg
      ln -s ${./setup.cfg} setup.cfg

      # generate MANIFEST.in to make sure every file is included
      rm -f MANIFEST.in
      cat > MANIFEST.in <<EOF
      recursive-include cli_common/*

      include VERSION
      include cli_common/VERSION
      include cli_common/*.ini
      include cli_common/*.json
      include cli_common/*.mako
      include cli_common/*.yml

      recursive-exclude * __pycache__
      recursive-exclude * *.py[co]
      EOF
    '';

    preConfigure = ''
      rm -rf build *.egg-info
    '';

    checkPhase = ''
      export LANG=en_US.UTF-8
      export LOCALE_ARCHIVE=${pkgs.glibcLocales}/lib/locale/locale-archive

      echo "################################################################"
      echo "## flake8 ######################################################"
      echo "################################################################"
      flake8 -v
      echo "################################################################"

      echo "################################################################"
      echo "## pytest ######################################################"
      echo "################################################################"
      pytest tests/ -vvv -s
      echo "################################################################"
    '';
  };

  # -- in alphabetic order --

  "async-timeout" = self: old: {
    patchPhase = ''
      sed -i -e "s|setup_requires=\['pytest-runner'\],||" setup.py
    '';
  };

  "awscli" = self: old: {
    propagatedBuildInputs = old.propagatedBuildInputs ++ (with pkgs; [ groff less ]);
    postInstall = ''
      mkdir -p $out/etc/bash_completion.d
      echo "complete -C $out/bin/aws_completer aws" > $out/etc/bash_completion.d/awscli
      mkdir -p $out/share/zsh/site-functions
      mv $out/bin/aws_zsh_completer.sh $out/share/zsh/site-functions
      rm $out/bin/aws.cmd
    '';
  };

  "chardet" = self: old: {
    patchPhase = ''
      sed -i -e "s|setup_requires=\['pytest-runner'\],||" setup.py
    '';
  };

  "clickclick" = self: old: {
    patchPhase = ''
      sed -i -e "s|setup_requires=\['six', 'flake8'\],||" setup.py
      sed -i -e "s|command_options=command_options,||" setup.py
    '';
  };

  "click-spinner" = self: old: {
    patchPhase = ''
      rm README.md
      touch README.md
    '';
  };

  "connexion" = self: old: {
    patchPhase = ''
      sed -i -e "s|setup_requires=\['flake8'\],||" setup.py
      sed -i -e "s|jsonschema>=2.5.1|jsonschema|" setup.py
      sed -i -e "s|'pathlib>=1.0.1; python_version < \"3.4\"',||" setup.py
    '';
  };

  "fancycompleter" = self: old: {
    patchPhase = ''
      sed -i -e "s|setup_requires=\['setuptools_scm'\],||" setup.py
    '';
  };

  "flake8" = self: old: {
    patchPhase = ''
      sed -i -e "s|setup_requires=\['pytest-runner'\],||" setup.py
    '';
  };

  "flask-talisman" = self: old: {
    # XXX: from https://github.com/GoogleCloudPlatform/flask-talisman/pull/8
    patchPhase = ''
      sed -i \
        -e "s|view_function = flask.current_app.view_functions\[|view_function = flask.current_app.view_functions.get(|" \
        -e "s|flask.request.endpoint\]|flask.request.endpoint)|" \
          flask_talisman/talisman.py
    '';
  };

  "gunicorn" = self: old: {
    patches = [
         (pkgs.fetchurl {
           url = "https://github.com/benoitc/gunicorn/pull/1527.patch";
           sha256 = "14zvlm4dh432gd5n32i2x60rkq3d8wz1xlj45ldkp2z4qgp7chbk";
         })
      ];
  };

  "jsonschema" = self: old: {
    patchPhase = ''
      sed -i -e 's|setup_requires=\["vcversioner>=2.16.0.0"\],||' setup.py
    '';
  };

  "libmozdata" = self: old: {
    # Remove useless dependencies
    patchPhase = ''
      sed -i -e "s|mercurial>=3.9.1; python_version < '3.0'||" requirements.txt
      sed -i -e "s|setuptools>=28.6.1||" requirements.txt
    '';
  };

  "mccabe" = self: old: {
    patchPhase = ''
      sed -i -e "s|setup_requires=\['pytest-runner'\],||" setup.py
    '';
  };

  "pdbpp" = self: old: {
    patchPhase = ''
      sed -i \
        -e "s|setup_requires=\['setuptools_scm'\],||" \
        -e "s|fancycompleter>=0.8|fancycompleter|" \
        setup.py
    '';
  };

  "pytest" = self: old: {
    patchPhase = ''
      sed -i -e "s|setup_requires=\['setuptools-scm'\],||" setup.py
    '';
  };

  "RBTools" = self: old: {
    patches = [
         (pkgs.fetchurl {
           url = "https://github.com/La0/rbtools/commit/190b4adb768897f65cf7ec57806649bc14c8e45d.diff";
           sha256 = "1hh6i3cffsc4fxr4jqlxralnf78529i0pspm7jn686a2s6bh26mw";
         })
      ];
  };
}
