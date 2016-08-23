{ releng_pkgs }:

let

  inherit (releng_pkgs.pkgs)
    cacert
    coreutils
    curl
    gnugrep
    gnused
    jq
    nix-prefetch-scripts
    writeScriptBin;
  inherit (releng_pkgs.pkgs.lib)
    flatten
    removeSuffix
    splitString
    unique;

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

in {

  packagesToUpdate = pkgs':
    builtins.filter
      (pkg: builtins.hasAttr "updateSrc" pkg)
      (builtins.attrValues pkgs');

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

  updateFromGitHub = { owner, repo, path, branch }:
    writeScriptBin "update" ''
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
