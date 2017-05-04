{ releng_pkgs 
}: 

let

  inherit (releng_pkgs.lib) mkTaskclusterHook mkPython fromRequirementsFile filterSource;
  inherit (releng_pkgs.pkgs) writeScript makeWrapper mercurial cacert ;
  inherit (releng_pkgs.pkgs.lib) fileContents optional licenses;
  inherit (releng_pkgs.tools) pypi2nix;

  python = import ./requirements.nix { inherit (releng_pkgs) pkgs; };
  name = "mozilla-shipit-pulse-listener";
  dirname = "shipit_pulse_listener";

  mercurial' = mercurial.overrideDerivation (old: {
    postInstall = old.postInstall + ''
      cat > $out/etc/mercurial/hgrc <<EOF
[web]
cacerts = ${cacert}/etc/ssl/certs/ca-bundle.crt

[extensions]
purge =
EOF
    '';
  });

  mkBot = branch:
    let
      secretsKey = "repo:github.com/mozilla-releng/services:branch:" + branch;
    in
      mkTaskclusterHook {
        name = "Triggers Taskcluster hooks on pulse messages";
        owner = "babadie@mozilla.com";
        schedule = [ "0 0 * * * *" ];  # every hour
        deadline = "1 hour";
        taskImage = self.docker;
        scopes = [
          ("secrets:get:" + secretsKey)

          # Needed to create tasks from hooks
          "hooks:trigger-hook:project-releng"
          "queue:create-task:aws-provisioner-v1/releng-task"
        ];
        taskEnv = {
          "SSL_CERT_FILE" = "${releng_pkgs.pkgs.cacert}/etc/ssl/certs/ca-bundle.crt";
        };
        taskCommand = [
          "/bin/shipit-pulse-listener"
          branch
          "--secrets"
          secretsKey
        ];
      };

  self = mkPython {
    inherit python name dirname;
    version = fileContents ./VERSION;
    src = filterSource ./. { inherit name; };
    buildInputs =
      fromRequirementsFile ./requirements-dev.txt python.packages;
    propagatedBuildInputs =
      fromRequirementsFile ./requirements.txt python.packages;
    postInstall = ''
      mkdir -p $out/bin
      ln -s ${mercurial'}/bin/hg $out/bin
    '';
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
        pushd ${self.src_path}
        ${pypi2nix}/bin/pypi2nix -v \
          -V 3.5 \
          -E "libffi openssl pkgconfig freetype.dev" \
          -r requirements.txt \
          -r requirements-dev.txt
        popd
      '';
    };
  };

in self
