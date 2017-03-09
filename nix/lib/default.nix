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
    nix
    stdenv
    writeScript;

  inherit (releng_pkgs.pkgs.lib)
    flatten
    inNixShell
    optional
    optionalAttrs
    optionals
    removeSuffix
    replaceStrings
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
      , cache ? {}
      }:
      { inherit env image features maxRunTime command artifacts cache; };

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
      , scopes ? []
      , cache ? {}
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
            cache = cache;
          };
          scopes = scopes;
        });
      };

  mkTaskclusterGithubTask =
    { name
    , branch
    , src_path
    , secrets ? "repo:github.com/mozilla-releng/services:branch:${branch}"
    }:
    ''
    # --- ${name} (${branch}) ---

      - metadata:
          name: "${name}"
          description: "Test, build and deploy ${name}"
          owner: "{{ event.head.user.email }}"
          source: "https://github.com/mozilla-releng/services/tree/${branch}/${src_path}"
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
                else "- pull_request.*\n          - push"}
            branches:
              - ${branch}
        provisionerId: "{{ taskcluster.docker.provisionerId }}"
        workerType: "{{ taskcluster.docker.workerType }}"
        payload:
          maxRunTime: 7200 # seconds (i.e. two hours)
          image: "nixos/nix:1.11"
          features:
            taskclusterProxy: true
          env:
            APP: "${name}"
            TASKCLUSTER_SECRETS: "taskcluster/secrets/v1/secret/${secrets}"
          command:
            - "/bin/bash"
            - "-c"
            - "nix-env -iA nixpkgs.gnumake nixpkgs.curl nixpkgs.cacert && export SSL_CERT_FILE=$HOME/.nix-profile/etc/ssl/certs/ca-bundle.crt && mkdir /src && cd /src && curl -L https://github.com/mozilla-releng/services/archive/$GITHUB_HEAD_SHA.tar.gz -o $GITHUB_HEAD_SHA.tar.gz && tar zxf $GITHUB_HEAD_SHA.tar.gz && cd services-$GITHUB_HEAD_SHA && ./.taskcluster.sh"
    '';

  fromRequirementsFile = file: custom_pkgs:
    let
      removeLines =
        builtins.filter
          (line: ! startsWith line "-r" && line != "" && ! startsWith line "#");

      removeExtras =
        builtins.map
          (line:
            let
              split = splitString "[" line;
            in
              if builtins.length split > 1
                then builtins.head split
                else line
          );

      extractEggName =
        map
          (line: 
            let
              split = splitString "egg=" line;
            in
              if builtins.length split == 2
                then builtins.elemAt split 1
                else line
          );

      readLines = file_:
        (splitString "\n"
          (removeSuffix "\n"
            (builtins.readFile file_)
          )
        );
    in
      map
        (pkg_name: builtins.getAttr pkg_name custom_pkgs)
        (removeExtras
          (removeLines
            (extractEggName
              (readLines file))));

        


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
      home_old=$HOME
      HOME=/tmp
      mkdir elm-stuff
      cat > elm-stuff/exact-dependencies.json <<EOF
      ${json}
      EOF
    '' + lib.concatStrings cmds + ''
      HOME=$home_old
    '';
       
  startsWith = s: x:
    builtins.substring 0 (builtins.stringLength x) s == x;

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
          "/build"
        ] else exclude;
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

  mkFrontend =
    { name
    , version
    , src
    , src_path ? "src/${name}"
    , csp ? "default-src 'none'; img-src 'self' data:; script-src 'self'; style-src 'self'; font-src 'self';"
    , nodejs
    , node_modules
    , elm_packages
    , patchPhase ? ""
    , postInstall ? ""
    , shellHook ? ""
    , inStaging ? true
    , inProduction ? false
    }:
    let
      scss_common = ./../../lib/scss_common;
      elm_common = ./../../lib/elm_common;
      self = stdenv.mkDerivation {
        name = "${name}-${version}";

        src = builtins.filterSource
          (path: type: baseNameOf path != "elm-stuff"
                    && baseNameOf path != "node_modules"
                    )
          src;

        buildInputs = [ nodejs elmPackages.elm ] ++ (builtins.attrValues node_modules);

        patchPhase = ''
          if [ -e src/scss ]; then
            rm \
              src/scss/fira \
              src/scss/font-awesome \
              src/scss/fonts.scss
            ln -s ${scss_common}/fira         ./src/scss/
            ln -s ${scss_common}/font-awesome ./src/scss/
            ln -s ${scss_common}/fonts.scss   ./src/scss/
          fi

          for item in ./*; do
            if [ -h $item ]; then
              rm -f $item
              cp ${elm_common}/`basename $item` ./
            fi
          done

          if [ -d src ]; then
            for item in ./src/*; do
              if [ -h $item ]; then
                rm -f $item
                cp ${elm_common}/`basename $item` ./src/
              fi
            done
          fi
        '' + patchPhase;

        configurePhase = ''
          rm -rf node_modules
          rm -rf elm-stuff
        '' + (makeElmStuff elm_packages) + ''
          mkdir node_modules
          for item in ${builtins.concatStringsSep " " (builtins.attrValues node_modules)}; do
            ln -s $item/lib/node_modules/* ./node_modules
          done
          export NODE_PATH=$PWD/node_modules:$NODE_PATH
        '';

        buildPhase = ''
          webpack
        '';

        doCheck = true;

        checkPhase = ''
          if [ -d src/ ]; then
            echo "----------------------------------------------------------"
            echo "---  Running ... elm-format-0.17 src/ --validate  --------"
            echo "----------------------------------------------------------"
            elm-format-0.17 src/ --validate
          fi
          if [ -e Main.elm ]; then
            echo "----------------------------------------------------------"
            echo "---  Running ... elm-format-0.17 ./*.elm --validate  -----"
            echo "----------------------------------------------------------"
            elm-format-0.17 ./*.elm --validate
          fi
          echo "Everything OK!"
          echo "----------------------------------------------------------"
        '';

        installPhase = ''
          mkdir $out
          cp build/* $out/ -R
          sed -i -e "s|<head>|<head>\n  <meta http-equiv=\"Content-Security-Policy\" content=\"${csp}\">|" $out/index.html
          runHook postInstall
        '';

        inherit postInstall;

        shellHook = ''
          cd ${src_path}
        '' + self.configurePhase + shellHook;

        passthru.taskclusterGithubTasks =
          map (branch: mkTaskclusterGithubTask { inherit name src_path branch; })
              ([ "master" ] ++ optional inStaging "staging"
                            ++ optional inProduction "production"
              );

        passthru.update = writeScript "update-${name}" ''
          export SSL_CERT_FILE="${cacert}/etc/ssl/certs/ca-bundle.crt"
          pushd ${src_path} >> /dev/null

          ${node2nix}/bin/node2nix \
            --composition node-modules.nix \
            --input node-modules.json \
            --output node-modules-generated.nix \
            --node-env node-env.nix \
            --flatten \
            --pkg-name nodejs-6_x

          # TODO: move this into default.nix
          ${gnused}/bin/sed -i -e "s| python2||" node-modules.nix
          ${gnused}/bin/sed -i -e "s| inherit nodejs;| python = pkgs.python2;inherit nodejs;|" node-modules.nix
          ${gnused}/bin/sed -i -e "s| sources.\"elm-0.18| #sources.\"elm-0.18|" node-modules-generated.nix
          ${gnused}/bin/sed -i -e "s| name = \"elm-webpack-loader\";| dontNpmInstall = true;name = \"elm-webpack-loader\";|" node-modules-generated.nix

          #rm -rf elm-stuff
          #${elmPackages.elm}/bin/elm-package install -y
          #${elm2nix}/bin/elm2nix elm-packages.nix

          popd
        '';
      };
    in self;

  mkBackend =
    args @
    { name
    , dirname
    , version
    , src
    , python
    , buildInputs ? []
    , propagatedBuildInputs ? []
    , doCheck ? true
    , postInstall ? ""
    , shellHook ? ""
    , dockerConfig ? {}
    , passthru ? {}
    , inStaging ? true
    , inProduction ? false
    }:
    let
      self = mkPython (args // {

        postInstall = ''
          mkdir -p $out/bin
          ln -s ${python.packages."Flask"}/bin/flask $out/bin
          ln -s ${python.packages."gunicorn"}/bin/gunicorn $out/bin
          ln -s ${python.packages."newrelic"}/bin/newrelic-admin $out/bin
          for i in $out/bin/*; do
            wrapProgram $i --set PYTHONPATH $PYTHONPATH
          done
          if [ -e ./settings.py ]; then
            mkdir -p $out/etc
            cp ./settings.py $out/etc
          fi
          if [ -d ./migrations ]; then
            mv ./migrations $out/${python.__old.python.sitePackages}
          fi
        '' + postInstall;

        shellHook = ''
          export CACHE_DEFAULT_TIMEOUT=3600
          export CACHE_TYPE=filesystem
          export CACHE_DIR=$PWD/cache
          export LANG=en_US.UTF-8
          export DEBUG=1
          export FLASK_APP=${dirname}:app
        '' + shellHook;

        dockerConfig = {
          Env = [
            "PATH=/bin"
            "APP_SETTINGS=${self}/etc/settings.py"
            "FLASK_APP=${dirname}:app"
            "LANG=en_US.UTF-8"
            "LOCALE_ARCHIVE=${glibcLocales}/lib/locale/locale-archive"
            "SSL_CERT_FILE=${releng_pkgs.pkgs.cacert}/etc/ssl/certs/ca-bundle.crt"
          ];
          Cmd = [
            "newrelic-admin" "run-program" "gunicorn" "${name}:app" "--log-file" "-"
          ];
        };

      });
    in self;

  mkPython =
    { name
    , dirname
    , version
    , src
    , python
    , buildInputs ? []
    , propagatedBuildInputs ? []
    , doCheck ? true
    , postInstall ? ""
    , shellHook ? ""
    , dockerConfig ?
      { Env = [
          "PATH=/bin"
          "LANG=en_US.UTF-8"
          "LOCALE_ARCHIVE=${releng_pkgs.pkgs.glibcLocales}/lib/locale/locale-archive"
          "SSL_CERT_FILE=${releng_pkgs.pkgs.cacert}/etc/ssl/certs/ca-bundle.crt"
        ];
        Cmd = [];
      }
    , passthru ? {}
    , inStaging ? true
    , inProduction ? false
    }:
    let

      self = python.mkDerivation {

        namePrefix = "";
        name = "${name}-${version}";

        inherit src;

        buildInputs =
          [ makeWrapper
            glibcLocales
          ] ++ buildInputs;

        propagatedBuildInputs =
          [ releng_pkgs.pkgs.cacert
          ] ++ propagatedBuildInputs;

        patchPhase = ''
          # replace synlink with real file
          rm VERSION
          echo ${version} > VERSION

          # generate MANIFEST.in to make sure every file is included
          rm -f MANIFEST.in
          cat > MANIFEST.in <<EOF
          recursive-include ${dirname}/*

          include VERSION
          include ${dirname}/*.ini
          include ${dirname}/*.json
          include ${dirname}/*.mako
          include ${dirname}/*.yml

          recursive-exclude * __pycache__
          recursive-exclude * *.py[co]
          EOF
        '';

        inherit doCheck;

        checkPhase = ''
          export LANG=en_US.UTF-8
          export LOCALE_ARCHIVE=${glibcLocales}/lib/locale/locale-archive

          flake8 --exclude=nix_run_setup.py,migrations/,build/
          pytest tests/
        '';

        postInstall = ''
          mkdir -p $out/bin
          ln -s ${python.__old.python.interpreter} $out/bin
          for i in $out/bin/*; do
            wrapProgram $i --set PYTHONPATH $PYTHONPATH
          done
          find $out -type d -name "__pycache__" -exec 'rm -r "{}"' \;
          find $out -type d -name "*.py" -exec '${python.__old.python.executable} -m compileall -f "{}"' \;
        '' + postInstall;

        shellHook = ''
          export LOCALE_ARCHIVE=${glibcLocales}/lib/locale/locale-archive

          pushd ${self.src_path} >> /dev/null
          tmp_path=$(mktemp -d)
          export PATH="$tmp_path/bin:$PATH"
          export PYTHONPATH="$tmp_path/${python.__old.python.sitePackages}:$PYTHONPATH"
          mkdir -p $tmp_path/${python.__old.python.sitePackages}
          ${python.__old.bootstrapped-pip}/bin/pip install -q -e . --prefix $tmp_path
          ${python.__old.bootstrapped-pip}/bin/pip install -q -e ../../lib/releng_common --prefix $tmp_path
          popd >> /dev/null

          cd ${self.src_path}
        '' + shellHook;

        passthru = {
          src_path =
            "src/" +
              (replaceStrings ["-"] ["_"]
                (builtins.substring 8
                  (builtins.stringLength name - 8) name));

          taskclusterGithubTasks =
            map (branch: mkTaskclusterGithubTask { inherit name branch; inherit (self) src_path; })
                ([ "master" ] ++ optional inStaging "staging"
                              ++ optional inProduction "production"
                );

          docker = mkDocker {
            inherit name version;
            contents = [ busybox self ];
            config = dockerConfig;
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
        ${nix}/bin/nix-prefetch-url \
           --unpack \
           "https://github.com/$1/$2/archive/$3.tar.gz" 2>&1 | \
               ${coreutils}/bin/tail -1
      }

      echo "=== ${owner}/${repo}@${branch} ==="

      echo "Looking up latest revision ... "
      rev=$(github_rev "${owner}" "${repo}" "${branch}");
      echo R"evision found: \`$rev\`."

      echo "Looking up sha256 ... "
      sha256=$(github_sha256 "${owner}" "${repo}" "$rev");
      echo "sha256 found: \`$sha256\`."

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
