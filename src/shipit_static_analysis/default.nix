{ releng_pkgs 
}: 

let

  inherit (releng_pkgs.lib) mkPython fromRequirementsFile filterSource ;
  inherit (releng_pkgs.pkgs) writeScript makeWrapper fetchurl dockerTools
      cacert clang llvmPackages_39 clang-tools rustStable;
  inherit (releng_pkgs.pkgs.stdenv) mkDerivation;
  inherit (releng_pkgs.pkgs.lib) fileContents optional licenses ;
  inherit (releng_pkgs.tools) pypi2nix mercurial;
  inherit (releng_pkgs.pkgs.pythonPackages) setuptools;

  python = import ./requirements.nix { inherit (releng_pkgs) pkgs; };
  name = "mozilla-shipit-static-analysis";
  dirname = "shipit_static_analysis";

  self = mkPython {
    inherit python name dirname;
    inProduction = true;
    version = fileContents ./../../VERSION;
    src = filterSource ./. { inherit name; };
    buildInputs =
      fromRequirementsFile ./requirements-dev.txt python.packages;
    propagatedBuildInputs =
      fromRequirementsFile ./requirements.txt python.packages
      ++ [
        # Needed for the static analysis
        clang
        clang-tools

        # Gecko environment
        releng_pkgs.gecko-env
      ];

    postInstall = ''
      mkdir -p $out/tmp
      mkdir -p $out/bin
      ln -s ${mercurial}/bin/hg $out/bin
      ln -s ${clang-tools}/bin/clang-tidy $out/bin
      ln -s ${llvmPackages_39.clang-unwrapped}/share/clang/run-clang-tidy.py $out/bin

      # Expose gecko env in final output
      ln -s ${releng_pkgs.gecko-env}/bin/gecko-env $out/bin
    '';

		shellHook = ''
			export PATH="${mercurial}/bin:$PATH"
		'';

    passthru = {
      taskclusterHooks = {
        master = {
        };
        staging = {
        };
        production = {
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
