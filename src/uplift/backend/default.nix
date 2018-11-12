{ releng_pkgs
}:

let

  inherit (releng_pkgs.lib) mkBackend2 fromRequirementsFile filterSource;
  inherit (releng_pkgs.pkgs) writeScript redis;
  inherit (releng_pkgs.pkgs.lib) fileContents;
  inherit (releng_pkgs.tools) pypi2nix;

  python = import ./requirements.nix { inherit (releng_pkgs) pkgs; };
  project_name = "uplift/backend";
  name = "mozilla-uplift-backend";
  dirname = "uplift_backend";
  src_path = "src/uplift/backend";

  self = mkBackend2 rec {
    inherit python name dirname src_path project_name;
    inProduction = true;
    version = fileContents ./VERSION;
    src = filterSource ./. { inherit name; };
    buildInputs =
      (fromRequirementsFile ./../../../lib/cli_common/requirements-dev.txt python.packages) ++
      (fromRequirementsFile ./../../../lib/backend_common/requirements-dev.txt python.packages) ++
      (fromRequirementsFile ./requirements-dev.txt python.packages) ++
      [ redis ];
    propagatedBuildInputs =
      (fromRequirementsFile ./requirements.txt python.packages);
    passthru = {
      update = writeScript "update-${name}" ''
        pushd ${self.src_path}
        ${pypi2nix}/bin/pypi2nix -v \
          -V 3.6 \
          -E "postgresql" \
          -r requirements.txt \
          -r requirements-dev.txt
        popd
      '';
    };
  };

in self
