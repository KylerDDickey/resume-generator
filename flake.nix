{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    systems.url = "github:nix-systems/default";
  };

  outputs =
    { systems, nixpkgs, ... }@inputs:
    let
      eachSystem = f: nixpkgs.lib.genAttrs (import systems) (system: f nixpkgs.legacyPackages.${system});
    in
    {
      devShells = eachSystem (pkgs: {
        default = pkgs.mkShell {
          buildInputs = [
            pkgs.gnumake
            pkgs.pandoc
            pkgs.pyright
            (pkgs.python312.withPackages (pypkgs: [
              pypkgs.jinja2
              pypkgs.watchdog
              pypkgs.weasyprint
              pypkgs.websockets
            ]))
          ];
        };
      });
    };
}
