{ releng_pkgs
}: 

let

  inherit (releng_pkgs.lib) mkTaskclusterGithubTask mkDocker mkTaskclusterHook filterSource;
  inherit (releng_pkgs.pkgs) writeScript makeWrapper;
  inherit (releng_pkgs.pkgs.lib) fileContents optional;
  inherit (releng_pkgs.tools) pypi2nix;

  python = import ./requirements.nix { inherit (releng_pkgs) pkgs; };

  mkPythonEnv =
    { name
    , version
    , src
    , src_path ? "src/${name}"
    , python
    , buildInputs ? []
    , propagatedBuildInputs ? []
    , passthru ? {}
    , staging ? true
    , production ? false
    }:
    let
      self = python.mkDerivation {
        namePrefix = "";
        name = "${name}-${version}";

        inherit src;

        buildInputs = [
          makeWrapper
          releng_pkgs.pkgs.glibcLocales
          python.packages."flake8"
        ] ++ buildInputs ;
        propagatedBuildInputs = [
          releng_pkgs.pkgs.cacert
        ] ++ propagatedBuildInputs;

        patchPhase = ''
          rm VERSION
          echo ${version} > VERSION
          rm -f MANIFEST.in
          cat > MANIFEST.in <<EOF
          recursive-include ${name}/*

          include VERSION
          include ${name}/*.ini
          include ${name}/*.json
          include ${name}/*.mako
          include ${name}/*.yml

          recursive-exclude * __pycache__
          recursive-exclude * *.py[co]
          EOF
        '';

        postInstall = ''
          mkdir -p $out/bin $out/etc

          ln -s ${python.__old.python.interpreter} $out/bin
       
          for i in $out/bin/*; do
            wrapProgram $i --set PYTHONPATH $PYTHONPATH
          done

          find $out -type d -name "__pycache__" -exec 'rm -r "{}"' \;
          find $out -type d -name "*.py" -exec '${python.__old.python.executable} -m compileall -f "{}"' \;
        '';

        doCheck = true;

        checkPhase = ''
          export LANG=en_US.UTF-8
          export LOCALE_ARCHIVE=${releng_pkgs.pkgs.glibcLocales}/lib/locale/locale-archive

          flake8 --exclude=nix_run_setup.py,migrations/,build/
          pytest tests/
        '';

        shellHook = ''
          export LOCALE_ARCHIVE=${releng_pkgs.pkgs.glibcLocales}/lib/locale/locale-archive

          pushd ${src_path} >> /dev/null
          tmp_path=$(mktemp -d)
          export PATH="$tmp_path/bin:$PATH"
          export PYTHONPATH="$tmp_path/${python.__old.python.sitePackages}:$PYTHONPATH"
          mkdir -p $tmp_path/${python.__old.python.sitePackages}
          ${python.__old.bootstrapped-pip}/bin/pip install -q -e . --prefix $tmp_path
          popd >> /dev/null

          cd ${src_path}
        '';

        passthru = {
          taskclusterGithubTasks =
            map (branch: mkTaskclusterGithubTask { inherit name src_path branch; })
                ([ "master" ] ++ optional staging "staging"
                              ++ optional production "production"
                );
          docker = mkDocker {
            inherit name version;
            contents = [ releng_pkgs.pkgs.busybox self ];
            config = {
              Env = [
                "PATH=/bin"
                "LANG=en_US.UTF-8"
                "LOCALE_ARCHIVE=${releng_pkgs.pkgs.glibcLocales}/lib/locale/locale-archive"
                "SSL_CERT_FILE=${releng_pkgs.pkgs.cacert}/etc/ssl/certs/ca-bundle.crt"
              ];
              Cmd = [];
            };
          };
        } // passthru;
      };
    in self;

  mkBot = branch :
    let
      cacheKey = "shipit-bot-" + branch;
      secretsKey = "project/shipit/bot/" + branch;
    in
      mkTaskclusterHook {
        name = "Shipit bot updating bug analysis";
        owner = "babadie@mozilla.com";
        schedule = [ "0 */30 * * * *" ];  # every 30 min
        taskImage = self.docker;
        scopes = [
          # Used by taskclusterProxy
          ("secrets:get:" + secretsKey)

          # Used by cache
          ("docker-worker:cache:" + cacheKey)
        ];
        cache = {
          "${cacheKey}" = "/cache";
        };
        taskEnv = {
          "SSL_CERT_FILE" = "${releng_pkgs.pkgs.cacert}/etc/ssl/certs/ca-bundle.crt";
        };
        taskCommand = [
          "/bin/shipit-bot-uplift"
          "--secrets"
          secretsKey
          "--cache-root"
          "/cache"
        ];
      };

  self = mkPythonEnv rec {
    inherit python ;
    production = true;
    name = "shipit_bot_uplift";
    version = fileContents ./../../VERSION;
    src = filterSource ./. { inherit name; };
    buildInputs =
      [ python.packages.flake8
        python.packages.pytest
        python.packages.ipdb
      ];
    propagatedBuildInputs =
      [ 
        python.packages.libmozdata
        python.packages.python-hglib
        python.packages.certifi
        python.packages.Logbook
        python.packages.structlog
        python.packages.click
        python.packages.mohawk
        python.packages.taskcluster
				releng_pkgs.pkgs.mercurial
      ];
    passthru = {
      taskclusterHooks = {
        master = {
        };
        staging = {
          bot = mkBot "staging";
        };
        production = {
          bot = mkBot "production";
        };
      };
      update = writeScript "update-${name}" ''
        pushd src/${name}
        ${pypi2nix}/bin/pypi2nix -v \
         -V 3.5 \
         -s "six packaging appdirs"
         -E "libffi openssl pkgconfig freetype.dev" \
         -r requirements.txt \
         -r requirements-dev.txt \
         -r requirements-nix.txt
        popd
      '';
    };
  };

in self
