# Your signing certificates

Drop your **own** certificate here and a card appears on the install page. One folder per certificate:

```
certs/
  My Cert/
    My Cert.p12                 (required — your distribution/enterprise certificate + private key)
    My Cert.mobileprovision     (required — a matching provisioning profile)
    password.txt                (optional — the .p12 password; else the P12_PASSWORD secret is used)
```

Only use certificates **you own**. A free Apple ID's development certificate cannot install apps
over-the-air onto other devices — that needs a distribution/enterprise certificate. Nothing is shipped
in this folder on purpose.
