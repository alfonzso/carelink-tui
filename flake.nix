{
  inputs.nixpkgs.url = "github:nixos/nixpkgs/nixos-26.05";

  outputs =
    { nixpkgs, ... }:
    let
      systems = [
        "x86_64-linux"
        "aarch64-linux"
      ];
      forAllSystems = nixpkgs.lib.genAttrs systems;
    in
    {
      packages = forAllSystems (
        system:
        let
          pkgs = import nixpkgs { inherit system; };
          metadata = builtins.fromJSON (builtins.readFile ./kdebar/metadata.json);
        in
        rec {
          carelink-kdebar = pkgs.stdenvNoCC.mkDerivation {
            pname = "carelink-kdebar";
            version = metadata.KPlugin.Version;
            src = ./kdebar;

            dontBuild = true;

            installPhase = ''
              runHook preInstall

              install -Dm644 metadata.json "$out/share/plasma/plasmoids/net.lehel.carelink.kdebar/metadata.json"
              cp -r contents "$out/share/plasma/plasmoids/net.lehel.carelink.kdebar/"
              install -Dm644 README.md "$out/share/doc/carelink-kdebar/README.md"

              runHook postInstall
            '';

            meta = {
              description = metadata.KPlugin.Description;
              homepage = metadata.KPlugin.Website;
              license = pkgs.lib.licenses.mit;
              platforms = pkgs.lib.platforms.linux;
            };
          };

          default = carelink-kdebar;
        }
      );
    };
}
