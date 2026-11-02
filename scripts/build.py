#!/usr/bin/env python3
"""Build the MuffinInstaller site.

Signs the latest MuffinEMU release with each certificate in certs/ (zsign), writes an itms-services
OTA manifest per certificate, and writes site/installer-data.json for the install page. With an empty
certs/ it records the current MuffinEMU version and an empty certificate list, so the page and the
Apple-ID path still publish. No certificates ship in this repo.

Approach based on SideInstaller by FrizzleM (https://github.com/FrizzleM/SideInstaller); independent,
non-commercial re-implementation for MuffinEMU.
"""
import datetime, glob, json, os, plistlib, subprocess, sys, urllib.request, zipfile

REPO_PAGES = "https://muffinemu.github.io/muffininstaller"
SIGNED_RELEASE = "https://github.com/MuffinEMU/muffininstaller/releases/download/signed"
BUNDLE_ID = "com.void.muffinemu"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE, CERTS, SIGNED = (os.path.join(ROOT, d) for d in ("site", "certs", "signed"))


def latest_release():
    req = urllib.request.Request(
        "https://api.github.com/repos/MuffinEMU/Muffin-EMU/releases/latest",
        headers={"Accept": "application/vnd.github+json", "User-Agent": "muffininstaller"})
    d = json.load(urllib.request.urlopen(req))
    ipa = next((a["browser_download_url"] for a in d["assets"] if a["name"] == "MuffinEMU.ipa"), None)
    return d["tag_name"].lstrip("v"), ipa


def provision_expiry(path):
    raw = open(path, "rb").read()
    i, j = raw.find(b"<?xml"), raw.rfind(b"</plist>")
    if i < 0 or j < 0:
        return None
    return plistlib.loads(raw[i:j + 8]).get("ExpirationDate")



def inject_marker(ipa_path):
    """Add an origin marker inside the .app so the installed copy knows MuffinInstaller signed it.
    It survives re-signing (ordinary bundle content); a plain SideStore/AltStore install won't have it."""
    with zipfile.ZipFile(ipa_path, "a") as z:
        app = next((n for n in z.namelist() if n.startswith("Payload/") and n.rstrip("/").endswith(".app")
                    and n.count("/") == 2 and n.endswith("/")), None)
        if not app:
            tops = {n.split("/")[1] for n in z.namelist() if n.startswith("Payload/") and "/" in n[8:]}
            app = "Payload/%s/" % next((t for t in tops if t.endswith(".app")), "")
        if app and app != "Payload/":
            if (app + "MuffinInstaller.origin") not in z.namelist():
                z.writestr(app + "MuffinInstaller.origin", b"MuffinInstaller\n")


def main():
    os.makedirs(os.path.join(SITE, "manifests"), exist_ok=True)
    version, ipa_url = latest_release()
    cert_dirs = sorted(d for d in glob.glob(os.path.join(CERTS, "*")) if os.path.isdir(d))

    if cert_dirs and ipa_url:
        os.makedirs(SIGNED, exist_ok=True)
        urllib.request.urlretrieve(ipa_url, os.path.join(SIGNED, "MuffinEMU.ipa"))
        inject_marker(os.path.join(SIGNED, "MuffinEMU.ipa"))

    certs = []
    for d in cert_dirs:
        name = os.path.basename(d)
        p12 = next(iter(glob.glob(os.path.join(d, "*.p12"))), None)
        prov = next(iter(glob.glob(os.path.join(d, "*.mobileprovision"))), None)
        if not p12 or not prov:
            continue
        pwd_file = os.path.join(d, "password.txt")
        pwd = open(pwd_file).read().strip() if os.path.exists(pwd_file) else os.environ.get("P12_PASSWORD", "")
        safe = name.replace(" ", "-").replace("/", "-")
        out = os.path.join(SIGNED, safe + ".ipa")
        r = subprocess.run(["zsign", "-k", p12, "-p", pwd, "-m", prov, "-o", out,
                            os.path.join(SIGNED, "MuffinEMU.ipa")], capture_output=True, text=True)
        if r.returncode != 0:
            print("sign failed for %s: %s" % (name, r.stderr[-400:]), file=sys.stderr)
            continue
        manifest = {"items": [{
            "assets": [{"kind": "software-package", "url": "%s/%s.ipa" % (SIGNED_RELEASE, safe)}],
            "metadata": {"bundle-identifier": BUNDLE_ID, "bundle-version": version,
                         "kind": "software", "title": "MuffinEMU %s" % version}}]}
        with open(os.path.join(SITE, "manifests", safe + ".plist"), "wb") as f:
            plistlib.dump(manifest, f)
        exp = provision_expiry(prov)
        days = (exp - datetime.datetime.now(exp.tzinfo)).days if exp else None
        certs.append({"name": name, "daysLeft": days,
                      "manifest": "%s/manifests/%s.plist" % (REPO_PAGES, safe)})

    certs.sort(key=lambda c: (c["daysLeft"] is None, -(c["daysLeft"] if c["daysLeft"] is not None else -9999)))
    data = {"version": version, "updated": datetime.datetime.utcnow().isoformat() + "Z", "certs": certs}
    with open(os.path.join(SITE, "installer-data.json"), "w") as f:
        json.dump(data, f, indent=2)
    print("built: MuffinEMU %s, %d certificate(s)" % (version, len(certs)))


if __name__ == "__main__":
    main()
