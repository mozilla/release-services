{ pkgs }:

self: old:

let
  inherit (pkgs.lib)
    flatten
    removeSuffix
    replaceStrings
    splitString
    unique;

  startsWith = s: x:
    builtins.substring 0 (builtins.stringLength x) s == x;

  fromRequirementsFile = file:
    let
      removeLines =
        builtins.filter
          (line: ! startsWith line "-r" && line != "" && ! startsWith line "#");

      removeAfter =
        delim: line:
          let
            split = splitString delim line;
          in
            if builtins.length split > 1
              then builtins.head split
              else line;

      removeSpaces =
        builtins.map (builtins.replaceStrings [" "]  [""]);

      removeExtras =
        builtins.map (removeAfter "[");

      removeComment =
        builtins.map (removeAfter "#");

      removeSpecs =
        builtins.map
          (line:
            (removeAfter "<" (
              (removeAfter ">" (
                (removeAfter ">=" (
                  (removeAfter "<=" (
                    (removeAfter "==" line))
                  ))
                ))
              ))
            ));

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
        (removeSpaces
          (removeComment
            (removeExtras
              (removeSpecs
                (removeLines
                  (extractEggName
                    (readLines file)))))));

  allDeps = builtins.attrNames self;
in {
  doCheck = true;
  buildInputs =
    builtins.map (name: self."${name}") (
      builtins.filter (name: builtins.elem name allDeps) (
        unique (
          flatten ((
            fromRequirementsFile ./../cli_common/requirements-dev.txt) ++ (
            fromRequirementsFile ./requirements-dev.txt) ++ (
              builtins.attrValues (
                builtins.fromJSON (
                  builtins.readFile ./requirements-extra.json)))))));
  patchPhase = ''
    # replace synlink with real file
    rm -f setup.cfg
    ln -s ${./../../nix/setup.cfg} setup.cfg

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
    pytest tests/ -vvv
    echo "################################################################"
  '';
}
