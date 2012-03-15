# CAdmin:
CAdmin is tool that should help maintain simple certification authority.

# Usage:
* Preconfigure CA

    ./install.py

* Create CA

    cp CA.cnf.def CA.cnf
    ./createca.py
    

* Create client certificate

    ./cln.py

* Create server certificate

    ./srv.py

* Create workstation certificate

    ./wrk.py
