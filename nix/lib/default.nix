{ releng_pkgs }:

let

  inherit (releng_pkgs.pkgs)
    busybox
    cacert
    coreutils
    curl
    dockerTools
    glibcLocales
    gnugrep
    gnused
    jq
    makeWrapper
    nix-prefetch-scripts
    stdenv
    writeScript;

  inherit (releng_pkgs.pkgs.lib)
    flatten
    inNixShell
    optionalAttrs
    optionals
    removeSuffix
    splitString
    unique;

  inherit (releng_pkgs)
    elmPackages;

  inherit (releng_pkgs.tools)
    pypi2nix
    elm2nix
    node2nix;

  ignoreRequirementsLines = specs:
    builtins.filter
      (x: x != "" &&                         # ignore all empty lines
          builtins.substring 0 1 x != "-" && # ignore all -r/-e
          builtins.substring 0 1 x != "#"    # ignore all comments
      )
      specs;

  cleanRequirementsSpecification = specs:
    let
      separators = [ "==" "<=" ">=" ">" "<" ];
      removeVersion = spec:
        let
          possible_specs =
            unique
              (builtins.filter
                (x: x != null)
                (map
                  (separator:
                    let
                      spec' = splitString separator spec;
                    in
                      if builtins.length spec' != 1
                      then builtins.head spec'
                      else null
                  )
                  separators
                )
              );
        in
          if builtins.length possible_specs == 1
          then builtins.head possible_specs
          else spec;
    in
      map removeVersion specs;

  migrate = import ./migrate.nix { inherit releng_pkgs; };

in rec {

  inherit (migrate) mysql2sqlite mysql2postgresql;

  packagesWith = attrName: pkgs':
    builtins.filter
      (pkg: builtins.hasAttr "name" pkg && builtins.hasAttr attrName pkg)
      (builtins.attrValues pkgs');

  mkDocker =
    { name
    , version
    , config ? {}
    , contents ? []
    }:
    dockerTools.buildImage {
      name = name;
      tag = version;
      fromImage = null;
      inherit contents config;
    };

    mkTaskclusterTaskMetadata =
      { name
      , description ? ""
      , owner
      , source ? "https://github.com/mozilla-releng/services"
      }:
      { inherit name description owner source; };

    mkTaskclusterTaskPayload =
      { image
      , command
      , maxRunTime ? 3600
      , features ? { taskclusterProxy = true; }
      , artifacts ? {}
      , env ? {}
      }:
      { inherit env image features maxRunTime command artifacts; };

    mkTaskclusterTask =
      { extra ? {}
      , metadata ? {}
      , payload ? {}
      , priority ? "normal"
      , provisionerId ? "aws-provisioner-v1"
      , retries ? 5
      , routes ? []
      , schedulerId ? "-"
      , scopes ? []
      , tags ? {}
      , workerType ? "releng-task"
      }:
      { inherit extra priority provisionerId retries routes schedulerId scopes
           tags workerType;
        payload = mkTaskclusterTaskPayload payload;
        metadata = mkTaskclusterTaskMetadata metadata;
      };

    mkTaskclusterHook =
      { name
      , description ? ""
      , owner
      , emailOnError ? true
      , schedule ? []
      , expires ? "1 month"
      , deadline ? "1 hour"
      , taskImage
      , taskCommand
      , taskArtifacts ? {}
      , taskEnv ? {}
      }:
      { inherit schedule expires deadline;
        metadata = { inherit name description owner emailOnError; };
        task = mkTaskclusterTask ({
          metadata = { inherit name description owner; };
          payload = mkTaskclusterTaskPayload {
            image = taskImage;
            command = taskCommand;
            artifacts = taskArtifacts;
            env = taskEnv;
          };
        });
      };

  mkTaskclusterGithubTask =
    { name
    , branch
    , secrets ? "repo:github.com/mozilla-releng/services:branch:${branch}"
    }:
    ''
    - metadata:
        name: "${name}"
        description: "Test, build and deploy ${name}"
        owner: "{{ event.head.user.email }}"
        source: "https://github.com/mozilla-releng/services/tree/${branch}/src/${name}"
      scopes:
        - secrets:get:${secrets}
        - hooks:modify-hook:project-releng/services-${branch}-${name}-*
        - assume:hook-id:project-releng/services-${branch}-${name}-*
      extra:
        github:
          env: true
          events:
            ${if branch == "staging" || branch == "production"
              then "- push"
              else "- pull_request.*\n        - push"}
          branches:
            - ${branch}
      provisionerId: "{{ taskcluster.docker.provisionerId }}"
      workerType: "{{ taskcluster.docker.workerType }}"
      payload:
        maxRunTime: 7200 # seconds (i.e. two hours)
        image: "nixos/nix:latest"
        features:
          taskclusterProxy: true
        env:
          APP: "${name}"
          TASKCLUSTER_SECRETS: "taskcluster/secrets/v1/secret/${secrets}"
        command:
          - "/bin/bash"
          - "-c"
          - "COMMAND"
    '';

  fromRequirementsFile = files: pkgs':
    let
      # read all files and flatten the dependencies
      # TODO: read recursivly all -r statements
      specs =
        flatten
          (map
            (file: splitString "\n"(removeSuffix "\n" (builtins.readFile file)))
            files
          );
    in
      map
        (requirement: builtins.getAttr requirement pkgs')
        (unique
          (cleanRequirementsSpecification
            (ignoreRequirementsLines
              specs
            )
          )
        );

  makeElmStuff = deps:
    let 
        inherit (releng_pkgs.pkgs) lib fetchurl;
        json = builtins.toJSON (lib.mapAttrs (name: info: info.version) deps);
        cmds = lib.mapAttrsToList (name: info: let
                 pkg = stdenv.mkDerivation {

                   name = lib.replaceChars ["/"] ["-"] name + "-${info.version}";

                   src = fetchurl {
                     url = "https://github.com/${name}/archive/${info.version}.tar.gz";
                     meta.homepage = "https://github.com/${name}/";
                     inherit (info) sha256;
                   };

                   phases = [ "unpackPhase" "installPhase" ];

                   installPhase = ''
                     mkdir -p $out
                     cp -r * $out
                   '';

                 };
               in ''
                 mkdir -p elm-stuff/packages/${name}
                 ln -s ${pkg} elm-stuff/packages/${name}/${info.version}
               '') deps;
    in ''
      export HOME=/tmp
      mkdir elm-stuff
      cat > elm-stuff/exact-dependencies.json <<EOF
      ${json}
      EOF
    '' + lib.concatStrings cmds;

  mkFrontend =
    { name
    , version
    , src
    , node_modules
    , elm_packages
    , patchPhase ? null
    , postInstall ? null
    }:
    let
      self = stdenv.mkDerivation {
        name = "${name}-${version}";
        src = builtins.filterSource
          (path: type: baseNameOf path != "elm-stuff"
                    && baseNameOf path != "node_modules"
                    )
          src;
        buildInputs = [ elmPackages.elm ] ++ (builtins.attrValues node_modules);
        configurePhase = ''
          rm -rf node_modules
          rm -rf elm-stuff
        '' + (makeElmStuff elm_packages) + ''
          mkdir node_modules
          for item in ${builtins.concatStringsSep " " (builtins.attrValues node_modules)}; do
            ln -s $item/lib/node_modules/* ./node_modules
          done
        '';
        buildPhase = ''
          neo build --config webpack.config.js
        '';
        installPhase = ''
          mkdir $out
          cp build/* $out/ -R
          runHook postInstall
        '';
        inherit postInstall patchPhase;
        shellHook = ''
          cd src/${name}
        '' + self.configurePhase;

        passthru.taskclusterGithubTasks =
          map (branch: mkTaskclusterGithubTask { inherit name branch; })
            [ "master" "staging" "production" ];
        passthru.update = writeScript "update-${name}" ''
          export SSL_CERT_FILE="${cacert}/etc/ssl/certs/ca-bundle.crt"
          pushd src/${name}
          ${node2nix}/bin/node2nix \
            --composition node-modules.nix \
            --input node-modules.json \
            --output node-modules-generated.nix \
            --node-env node-env.nix \
            --flatten \
            --pkg-name nodejs-6_x
          rm -rf elm-stuff
          ${elmPackages.elm}/bin/elm-package install -y
          ${elm2nix}/bin/elm2nix elm-packages.nix
          popd
        '';
      };
    in self;

  filterSource = src:
    { name ? null
    , include ? [ "/" ]
    , exclude ? []
    }:
      assert name == null -> include != null;
      assert name == null -> exclude != null;
      let
        _include= if include == null then [
          "/VERSION"
          "/${name}"
          "/tests"
          "/MANIFEST.in"
          "/settings.py"
          "/setup.py"
        ] else include;
        _exclude = if exclude == null then [
            "/${name}.egg-info"
        ] else exclude;
        startsWith = s: x: builtins.substring 0 (builtins.stringLength x) s == x;
        relativePath = path:
          builtins.substring (builtins.stringLength (builtins.toString src))
                             (builtins.stringLength path)
                             path;
      in
        builtins.filterSource (path: type: 
          if builtins.any (x: x) (builtins.map (startsWith (relativePath path)) _exclude) then false
          else if builtins.any (x: x) (builtins.map (startsWith (relativePath path)) _include) then true
          else false
        ) src;

  mkBackend =
    { name
    , version
    , src
    , python
    , buildInputs ? []
    , propagatedBuildInputs ? []
    , passthru ? {}
    }:
    let
      self = python.mkDerivation {
        namePrefix = "";
        name = "${name}-${version}";

        inherit src;

        buildInputs = [
          makeWrapper
          glibcLocales
          python.packages."flake8"
          python.packages."gunicorn"
        ] ++ buildInputs;
        propagatedBuildInputs = [] ++ propagatedBuildInputs;

        patchPhase = ''
          rm -f VERSION
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
          cat MANIFEST.in
          ls -la
          pwd
        '';

        postInstall = ''
          mkdir -p $out/bin $out/etc

          ln -s ${python.__old.python.interpreter} $out/bin
          ln -s ${python.packages."Flask"}/bin/flask $out/bin
          ln -s ${python.packages."gunicorn"}/bin/gunicorn $out/bin
          ln -s ${python.packages."newrelic"}/bin/newrelic-admin $out/bin
       
          cp ./settings.py $out/etc

          for i in $out/bin/*; do
            wrapProgram $i --set PYTHONPATH $PYTHONPATH
          done

          for i in $out/${python.__old.python.sitePackages}/*; do
            if test -e $i/__pycache__; then
              rm -rf $i/__pycache__
            fi
            ${python.__old.python.executable} -m compileall -f $i
          done

          exit 123

        '';

        checkPhase = ''
          export LANG=en_US.UTF-8
          export LOCALE_ARCHIVE=${glibcLocales}/lib/locale/locale-archive

          flake8 --exclude=nix_run_setup.py,migrations/,build/
          pytest tests/
        '';

        shellHook = ''
          export CACHE_DEFAULT_TIMEOUT=3600
          export CACHE_TYPE=filesystem
          export CACHE_DIR=$PWD/cache
          export LANG=en_US.UTF-8
          export FLASK_APP=${name}
          export DEBUG=1
          export LOCALE_ARCHIVE=${glibcLocales}/lib/locale/locale-archive
          export FLASK_APP=${name}:app

          pushd src/${name}
          tmp_path=$(mktemp -d)
          export PATH="$tmp_path/bin:$PATH"
          export PYTHONPATH="$tmp_path/${python.__old.python.sitePackages}:$PYTHONPATH"
          mkdir -p $tmp_path/${python.__old.python.sitePackages}
          ${python.__old.bootstrapped-pip}/bin/pip install -q -e . --prefix $tmp_path
          ${python.__old.bootstrapped-pip}/bin/pip install -q -e ../../lib/releng_common --prefix $tmp_path
          popd >> /dev/null
        '';

        passthru = {
          taskclusterGithubTasks =
            map (branch: mkTaskclusterGithubTask { inherit name branch; })
                [ "master" "staging" "production" ];
          docker = mkDocker {
            inherit name version;
            contents = [ busybox self ];
            config = {
              Env = [
                "PATH=/bin"
                "APP_SETTINGS=${self}/etc/settings.py"
                "FLASK_APP=${name}:app"
                "LANG=en_US.UTF-8"
                "LOCALE_ARCHIVE=${glibcLocales}/lib/locale/locale-archive"
              ];
              Cmd = [
                "newrelic-admin" "run-program" "gunicorn" "${name}:app" "--log-file" "-"
              ];
            };
          };
        } // passthru;
      };
    in self;

  updateFromGitHub = { owner, repo, path, branch }:
    writeScript "update-from-github-${owner}-${repo}-${branch}" ''
      export SSL_CERT_FILE=${cacert}/etc/ssl/certs/ca-bundle.crt

      github_rev() {
        ${curl.bin}/bin/curl -sSf "https://api.github.com/repos/$1/$2/branches/$3" | \
          ${jq}/bin/jq '.commit.sha' | \
          ${gnused}/bin/sed 's/"//g'
      }

      github_sha256() {
        ${nix-prefetch-scripts}/bin/nix-prefetch-zip \
           --hash-type sha256 \
           "https://github.com/$1/$2/archive/$3.tar.gz" 2>&1 | \
           ${gnugrep}/bin/grep "hash is " | \
           ${gnused}/bin/sed 's/hash is //'
      }

      echo "=== ${owner}/${repo}@${branch} ==="

      echo -n "Looking up latest revision ... "
      rev=$(github_rev "${owner}" "${repo}" "${branch}");
      echo "revision is \`$rev\`."

      sha256=$(github_sha256 "${owner}" "${repo}" "$rev");
      echo "sha256 is \`$sha256\`."

      if [ "$sha256" == "" ]; then
        echo "sha256 is not valid!"
        exit 2
      fi
      source_file=$HOME/${path}
      echo "Content of source file (``$source_file``) written."
      cat <<REPO | ${coreutils}/bin/tee "$source_file"
      {
        "owner": "${owner}",
        "repo": "${repo}",
        "rev": "$rev",
        "sha256": "$sha256"
      }
      REPO
      echo
    '';
}
