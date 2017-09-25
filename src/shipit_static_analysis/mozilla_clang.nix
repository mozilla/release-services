{ releng_pkgs }:

let
  inherit (releng_pkgs.pkgs) fetchurl gnutar llvmPackages_4;
  inherit (releng_pkgs.pkgs.stdenv) mkDerivation;
  inherit (releng_pkgs.pkgs.lib) licenses ;

  clang = llvmPackages_4.clang-unwrapped;

  # Retrieve Mozilla clang-plugin from mozilla central
  moz_clang_plugin = mkDerivation rec {
    name = "moz-clang-plugin";
    revision = "47f7b6c64265";

    src = fetchurl {
      url = "https://hg.mozilla.org/mozilla-central/archive/${revision}.tar.bz2/build/clang-plugin";
      sha256 = "0nxzk08sz7vpqmxcvhxf12immdflvsg1yhmlkr5smmvjv0bmm0s5";
    };

    third_party = fetchurl {
      url = "https://hg.mozilla.org/mozilla-central/raw-file/${revision}/tools/rewriting/ThirdPartyPaths.txt";
      sha256 = "1fna1577clw6sm6x28mz8pdkhs4hzi1xycjynpbq8xi5v3n9zhj9";
    };

    # Skip first directories with revision
    unpackCmd = ''
      ${gnutar}/bin/tar -xf $curSrc --strip 1
    '';

    patchPhase = ''
      # generate ThirdPartyPaths.cpp
      # No trailing /
      # Embed in quotes for cpp array
      third=$(sed "s/\/$//" ${third_party} | sed -e "s/\(.*\)$/\"\1\",/")
      nb_third=$(wc -l ${third_party} | awk '{print $1}')
      echo "#include <stdint.h>
const char* MOZ_THIRD_PARTY_PATHS[] = { $third };
extern const uint32_t MOZ_THIRD_PARTY_PATHS_COUNT = $nb_third;
" > clang-plugin/ThirdPartyPaths.cpp

      # generate CMakeLists.txt with list of cpp (write_cmake)
      cpps=$(cd clang-plugin && ls *.cpp)
      echo "set(LLVM_LINK_COMPONENTS support)

add_definitions( -DCLANG_TIDY )
add_definitions( -DHAVE_NEW_ASTMATCHER_NAMES )

add_clang_library(clangTidyMozillaModule
  ThirdPartyPaths.cpp
  $cpps

  LINK_LIBS
  clangAST
  clangASTMatchers
  clangBasic
  clangLex
  clangTidy
  clangTidyReadabilityModule
  clangTidyUtils
)" > clang-plugin/CMakeLists.txt

    '';

    installPhase = ''
      mkdir -p $out
      mv clang-plugin/* $out
    '';

    buildInputs = [gnutar];
    propagatedBuildInputs = [ ];
    meta = {
      homepage = "https://hg.mozilla.org/hgcustom/version-control-tools";
      license = licenses.mit;
      description = "https://developer.mozilla.org/en-US/docs/Mozilla/Testing/Clang_static_analysis";
    };
  };

  self = clang.overrideDerivation (old: {
    # Add mozilla clang-plugin source for clang-tidy
    buildInputs = old.buildInputs ++ [moz_clang_plugin];
    unpackPhase = old.unpackPhase + ''
      dest=$sourceRoot/tools/extra/clang-tidy/mozilla
      mkdir $dest
      cp -rf ${moz_clang_plugin}/* $dest
    '';

    # Patch Cmake files, as is described in
    # https://dxr.mozilla.org/mozilla-central/source/build/clang-plugin/import_mozilla_checks.py
    postPatch = old.postPatch + ''

      # Add clangTidyMozillaModule to LINK_LIBS
      target=$sourceRoot/tools/extra/clang-tidy/plugin/CMakeLists.txt
      sed '/LINK_LIBS/a \ \ clangTidyMozillaModule' -i $target

      # Add clangTidyMozillaModule to target_link_libraries
      target=$sourceRoot/tools/extra/clang-tidy/tool/CMakeLists.txt
      sed '/target_link_libraries(clang-tidy/a \ \ clangTidyMozillaModule' -i $target

      # Activate plugin
      target=$sourceRoot/tools/extra/clang-tidy/CMakeLists.txt
      echo 'add_subdirectory(mozilla)' >> $target

      # Add inline patch
      target=$sourceRoot/tools/extra/clang-tidy/tool/ClangTidyMain.cpp
      echo '// This anchor is used to force the linker to link the MozillaModule.' >> $target
      echo 'extern volatile int MozillaModuleAnchorSource;' >> $target
      echo 'static int LLVM_ATTRIBUTE_UNUSED MozillaModuleAnchorDestination = MozillaModuleAnchorSource;' >> $target
    '';
  });

in
  self
