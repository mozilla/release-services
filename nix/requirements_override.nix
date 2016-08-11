{ pkgs, python }:

self: super: {

  "awscli" = python.overrideDerivation super."awscli" (old: {
    propagatedBuildInputs = old.propagatedBuildInputs ++ (with pkgs; [ groff less ]);
    postInstall = ''
      mkdir -p $out/etc/bash_completion.d
      echo "complete -C $out/bin/aws_completer aws" > $out/etc/bash_completion.d/awscli
      mkdir -p $out/share/zsh/site-functions
      mv $out/bin/aws_zsh_completer.sh $out/share/zsh/site-functions
      rm $out/bin/aws.cmd
    '';
  });
}
