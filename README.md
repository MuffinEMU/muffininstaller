# MuffinInstaller

Install **MuffinEMU** (Wii U emulation for iPhone and iPad) straight from the web — no computer —
or with your own Apple ID. Live at **https://muffinemu.github.io/MuffinInstaller/**.

Two ways, both on `index.html`:

1. **One tap, from the web.** The install page shows a card per signing certificate in `certs/`.
   Tapping one installs MuffinEMU on-device over `itms-services` (OTA). **No certificates ship in this
   repo** — add your **own** (see `certs/README.md`) and a card appears. A free Apple ID cannot do this
   (it needs a distribution/enterprise certificate you own); use path 2 instead if you don't have one.
2. **With your own Apple ID.** Once MuffinEMU is installed, the built-in MuffinInstaller
   (Settings > Storage > MuffinInstaller) signs, renews and updates it with your own Apple ID — the
   legitimate, no-enterprise-cert path.

## How it's built

`.github/workflows/publish.yml` runs `scripts/build.py`: it reads the latest MuffinEMU release,
signs it with each certificate in `certs/` (zsign), writes an `itms-services` manifest per cert and a
`site/installer-data.json` the page reads, then deploys `site/` to GitHub Pages. With an empty `certs/`
it just publishes the page and the Apple-ID path.

## Credit & licence

The on-device web-install idea and approach are based on **SideInstaller by FrizzleM**
(https://github.com/FrizzleM/SideInstaller). This is an independent, non-commercial implementation for
MuffinEMU. No certificates, and no third-party signed builds, are redistributed here.
