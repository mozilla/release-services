{ releng_pkgs }:

let

  inherit (releng_pkgs) pkgs;

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
            pkgs.lib.unique
              (builtins.filter
                (x: x != null)
                (map
                  (separator:
                    let
                      spec' = pkgs.lib.splitString separator spec;
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

  from_requirements = files: pkgs':
    let
      # read all files and flatten the dependencies
      # TODO: read recursivly all -r statements
      specs =
        pkgs.lib.flatten
          (map
            (file: pkgs.lib.splitString "\n"(pkgs.lib.removeSuffix "\n" (builtins.readFile file)))
            files
          );
    in
      map
        (requirement: builtins.getAttr requirement pkgs')
        (pkgs.lib.unique
          (cleanRequirementsSpecification
            (ignoreRequirementsLines
              specs
            )
          )
        );

}
