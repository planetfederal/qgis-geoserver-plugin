Boundless Test PKI Certificates/Keys
------------------------------------

The certs/keys are generated/edited using **XCA** (see xca-project directory):

    https://sourceforge.net/projects/xca/

The Java keystore files are generated/edited using **KeyStore Explorer**:

    http://keystore-explorer.sourceforge.net/


The generic default password for encrypted components, the XCA project and the Java keystore files is **password**. The certificate signing structure can be reviewed in `certs_hierarchy.png`.

WARNING: these PKI components are just for testing and should _NOT_ be used in a production environment.

**Client connections:**

* User certs: `[alice|tom|jane|joe]-cert.[crt|pem]`

* User keys:  `[alice|tom|jane|joe]-key.[key|pem]`

* Combined CAs: `subissuer-issuer-root-ca_issuer-2-root-2-ca_chains.[crt|pem]` The root certs are self-signed, so you will need to have these two CA chains _trusted_ in your cert/key store or passed during connections, so as to validate the certificate of the connected server.

NOTE: the `.[crt|pem]` choice is because some applications filter file open dialogs to specific extensions, e.g. pgAdmin3 always filters `.crt` or `.key` and QGIS generally filters on `.pem`.

**Server configurations:**

Two certificates are available for general SSL/TLS servers:

* `server-localhost-cert.[crt|pem]` for **localhost** servers accessed from the same host.

* `server-boundless-test-cert.[crt|pem]` provides for a **boundless-test** domain, which can be associated locally with an IP address from a VM or docker container using the host OS's `hosts` file. This setup allows for testing where a remote _localhost_ domain will usually result in a 'hostname mismatch' SSL error from clients.

* Both are signed under the `issuer-root-ca-chain.[crt|pem]` certificates.
