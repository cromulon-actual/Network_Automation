#! bin/python
###############################################################################
# Requirements to run the script are as follows:
# 1. Must have entered environment variables for Domain, Country, State, City,
#    ORG, and OU
# 2. Must have nornir setup with list of devices in group labeled 'infrastructure'
# 3. File path created: 'local_files/csr/keys'
###############################################################################
## To be used in refactoring ##
import sys
import platform
import yaml
import argparse
import logging

# Currently Used
import os
import logging.handlers
from OpenSSL import crypto

from nornir import InitNornir
from nornir.core.filter import F


nr = InitNornir("files/config.yaml")
infrastructure = nr.filter(F(groups__contains='infrastructure'))


# DOMAIN = os.environ['DOMAIN']  # .domain.com
# COUNTRY = os.environ['COUNTRY']  # US
# STATE = os.environ['STATE']  # Florida
# CITY = os.environ['CITY']  # Miami
# ORG = os.environ['ORGANIZATION']  # CompanyXYZ
# OU = os.environ['OU']  # IT

DOMAIN = 'carcgl.com'  # .domain.com
COUNTRY = 'US'  # US
STATE = 'FL'  # Florida
CITY = 'Palm Beach Gardens'  # Miami
ORG = 'Carrier'  # CompanyXYZ
OU = 'IT'  # IT


def create_csr(common_name, country=None, state=None, city=None,
               organization=None, organizational_unit=None,
               email_address=None):
    """
    Args:
        common_name (str).

        country (str).

        state (str).

        city (str).

        organization (str).

        organizational_unit (str).

        email_address (str).

    Returns:
        (str, str).  Tuple containing private key and certificate
        signing request (PEM).
    """
    key = crypto.PKey()
    key.generate_key(crypto.TYPE_RSA, 2048)

    req = crypto.X509Req()
    req.get_subject().CN = common_name
    if country:
        req.get_subject().C = country
    if state:
        req.get_subject().ST = state
    if city:
        req.get_subject().L = city
    if organization:
        req.get_subject().O = organization
    if organizational_unit:
        req.get_subject().OU = organizational_unit
    if email_address:
        req.get_subject().emailAddress = email_address

    req.set_pubkey(key)
    req.sign(key, 'sha256')

    private_key = crypto.dump_privatekey(
        crypto.FILETYPE_PEM, key)

    csr = crypto.dump_certificate_request(
        crypto.FILETYPE_PEM, req)

    public_key = crypto.dump_publickey(crypto.FILETYPE_PEM, key)

    return private_key, csr, public_key


for host in infrastructure.inventory.hosts:
    private_key, csr, public_key = create_csr(f'{host}{DOMAIN}', country=COUNTRY, state=STATE,
                                              city=CITY, organization=ORG, organizational_unit=OU)

    with open(f'local_files/csr/keys/{host}.pem', 'wb') as f:
        f.write(private_key)
        f.write(public_key)

    with open(f'local_files/csr/{host}.csr', 'wb') as f:
        f.write(csr)
