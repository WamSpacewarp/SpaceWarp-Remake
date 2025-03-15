{ pkgs, lib, config, inputs, ... }:

let
  libraries = with pkgs; [
    SDL2
  ];
in
{
  # https://devenv.sh/basics/
  env = {
    LD_LIBRARY_PATH = lib.makeLibraryPath libraries;
    GREET = "devenv";
  };

  # https://devenv.sh/packages/
  packages = with pkgs; [ 
    git
  ] ++ libraries;

  # https://devenv.sh/languages/
  # languages.rust.enable = true;
  languages.python = {
    enable = true;
    version = "3.13";
    venv = {
      enable = true;
      requirements = builtins.readFile ./requirements.txt;
    };
    uv.enable = true;
  };

  # https://devenv.sh/processes/
  # processes.cargo-watch.exec = "cargo-watch";

  # https://devenv.sh/services/
  # services.postgres.enable = true;

  # https://devenv.sh/scripts/
  # scripts.hello.exec = ''
  #   echo hello from $GREET
  # '';

  # enterShell = ''
  #   hello
  #   git --version
  # '';

  # https://devenv.sh/tasks/
  # tasks = {
  #   "myproj:setup".exec = "mytool build";
  #   "devenv:enterShell".after = [ "myproj:setup" ];
  # };

  # https://devenv.sh/tests/
  # enterTest = ''
  #   echo "Running tests"
  #   git --version | grep --color=auto "${pkgs.git.version}"
  # '';

  # https://devenv.sh/pre-commit-hooks/
  # pre-commit.hooks.shellcheck.enable = true;

  # See full reference at https://devenv.sh/reference/options/
}
