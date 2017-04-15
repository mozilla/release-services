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
    # TODO: doCheck = true;
    buildInputs =
      [ self."flake8"
        self."pytest"
        self."responses"
      ];
    preConfigure = ''
      rm -rf build *.egg-info
    '';
    checkPhase = ''
      flake8 --exclude=nix_run_setup.py,migrations/,build/
      pytest tests
    '';
  };

  "mozilla-cli-common" = self: old: {
    name = "mozilla-cli-common-${fileContents ./../lib/backend_common/VERSION}";
    buildInputs =
      [ self."flake8"
        self."pytest"
      ];
    preConfigure = ''
      rm -rf build *.egg-info
    '';
    # TODO: doCheck = true;
    checkPhase = ''
      flake8 --exclude=nix_run_setup.py,build/
      pytest tests
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

  "connexion" = self: old: {
    patchPhase = ''
      sed -i -e "s|setup_requires=\['flake8'\],||" setup.py
      sed -i -e "s|jsonschema>=2.5.1|jsonschema|" setup.py
    '';
  };

  "flake8" = self: old: {
    patchPhase = ''
      sed -i -e "s|setup_requires=\['pytest-runner'\],||" setup.py
    '';
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

  "flask-talisman" = self: old: {
    # XXX: from https://github.com/GoogleCloudPlatform/flask-talisman/pull/8
    patchPhase = ''
      sed -i \
        -e "s|view_function = flask.current_app.view_functions\[|view_function = flask.current_app.view_functions.get(|" \
        -e "s|flask.request.endpoint\]|flask.request.endpoint)|" \
          flask_talisman/talisman.py
    '';
  };

}
