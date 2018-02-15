#!/usr/bin/python
# -*- coding: utf-8 -*-
# https://github.com/rmin

DOCUMENTATION = '''
---
module: dnszone
short_description: For updating DNS Zone files with input validation for each record type
description:
    - Make sure a record is present/absent on a Zone file
author:
    - Armin Ranjbar Daemi https://github.com/rmin
notes:
    - Tested on Ansible 2
requirements:
    - python >= 2.6
    - dns
options:
    file:
        description:
            - Path to the zone file
        required: True
    domain:
        description:
            - Origin domain of the zone
        required: True
    type:
        description:
            - Type of the DNS record
        default: A
        choices: ["NS", "A", "AAAA", "MX", "CNAME", "TXT"]
        required: False
    name:
        description:
            - Name of the DNS record
        required: True
    data:
        description:
            - Data of the DNS record
        default: ""
        required: False
    ttl:
        description:
            - TTL of the DNS record
        default: "86400"
        required: False
    state:
        description:
            - Add or remove the record
        default: "present"
        choices: ["present", "absent"]
        required: False
    relativize:
        description:
            - Relativize the Zone file to Origin domain
        default: True
        required: False
    updateserial:
        description:
            - Update SOA serial before saving changes to Zone file
        default: True
        required: False
'''

EXAMPLES = '''
- name: Add one A record
    dnszone:
        file: /vagrant/sample.zone
        domain: mydomain.com
        type: A
        name: testing1
        data: 192.168.1.1
        ttl: 4800
        relativize: true
        state: present
    register: debug_result
- name: Remove one A record
    dnszone:
        file: /vagrant/sample.zone
        domain: mydomain.com
        type: A
        name: testing1.mydomain.com.
        state: absent
    register: debug_result
- name: Add one MX record
    dnszone:
        file: /vagrant/sample.zone
        domain: mydomain.com
        type: MX
        name: mydomain.com.
        data: 20 mailtest
        state: present
- name: Add one TXT record
    dnszone:
        file: /vagrant/sample.zone
        domain: mydomain.com
        type: TXT
        name: txt3
        data: test value!
        ttl: 3600
        state: present
'''

from ansible.module_utils.basic import *
try:
    import dns.zone, dns.rdata, json, os
    from dns.exception import DNSException
    from dns.rdataclass import *
    from dns.rdatatype import *
    from dns.rdtypes.ANY import *
    from dns.rdtypes.IN import *
    HAS_DNSPYTHON = True
except ImportError:
    HAS_DNSPYTHON = False

class DnsZone(object):

    def __init__(self, zone_file, domain, relativize):
        self.relativize = relativize
        self.domain = domain
        self.zone_file = zone_file
        self.rtypes = ["NS", "A", "AAAA", "MX", "CNAME", "TXT"]
        self.zone = dns.zone.from_file(zone_file, domain, relativize=relativize)

    def save(self):
        self.zone.to_file(self.zone_file, relativize=self.relativize)

    def getRecords(self):
        res = []
        for rtype in self.rtypes:
            for (name, ttl, rdata) in self.zone.iterate_rdatas(rtype):
                res.append({"type":str(rtype), "name":str(name), "data":str(rdata), "ttl":str(ttl)})
        return res

    def increaseSOASerial(self):
        for (name, ttl, rdata) in self.zone.iterate_rdatas(dns.rdatatype.SOA):
            rdata.serial = rdata.serial + 1

    def delRecord(self, _type, _name):
        rds = self.zone.get_rdataset(_name, rdtype=_type)
        if rds:
            self.zone.delete_rdataset(_name, _type)
            return True
        return False

    def addRecord(self, _type, _name, _data, _ttl):
        if _type == "A":
            rdataset = self.zone.get_rdataset(_name, rdtype=dns.rdatatype.A, create=True)
            rdata = dns.rdtypes.IN.A.A(dns.rdataclass.IN, dns.rdatatype.A, address=_data)
            rdataset.add(rdata, ttl=int(_ttl))
            return True
        if _type == "AAAA":
            rdataset = self.zone.get_rdataset(_name, rdtype=dns.rdatatype.AAAA, create=True)
            rdata = dns.rdtypes.IN.AAAA.AAAA(dns.rdataclass.IN, dns.rdatatype.AAAA, address=_data)
            rdataset.add(rdata, ttl=int(_ttl))
            return True
        if _type == "NS":
            rdataset = self.zone.get_rdataset(_name, rdtype=NS, create=True)
            rdata = dns.rdtypes.ANY.NS.NS(dns.rdataclass.IN, dns.rdatatype.NS, dns.name.Name((_data,)))
            rdataset.add(rdata, ttl=int(_ttl))
            return True
        if _type == "MX":
            preference,exchange = _data.split(" ")
            rdataset = self.zone.get_rdataset(_name, rdtype=dns.rdatatype.MX, create=True)
            rdata = dns.rdtypes.ANY.MX.MX(dns.rdataclass.IN, dns.rdatatype.MX, int(preference), dns.name.Name((exchange,)))
            rdataset.add(rdata, ttl=int(_ttl))
            return True
        if _type == "CNAME":
            rdataset = self.zone.get_rdataset(_name, rdtype=dns.rdatatype.CNAME, create=True)
            rdata = dns.rdtypes.ANY.CNAME.CNAME(dns.rdataclass.IN, dns.rdatatype.CNAME, dns.name.Name((_data,)))
            rdataset.add(rdata, ttl=int(_ttl))
            return True
        if _type == "TXT":
            rdataset = self.zone.get_rdataset(_name, rdtype=dns.rdatatype.TXT, create=True)
            rdata = dns.rdtypes.ANY.TXT.TXT(dns.rdataclass.IN, dns.rdatatype.TXT, strings=_data.split(';'))
            rdataset.add(rdata, ttl=int(_ttl))
            return True
        return False

def state_present(data=None):
    try:
        wzone = DnsZone(data['file'], data['domain'], data['relativize'])
    except Exception, e:
        return (False, "Can not open zone file.")
    has_changed = wzone.addRecord(data['type'], data['name'], data['data'], data['ttl'])
    if has_changed:
        if data['updateserial']:
            wzone.increaseSOASerial()
        wzone.save()
    return (has_changed, wzone.getRecords())

def state_absent(data=None):
    try:
        wzone = DnsZone(data['file'], data['domain'], data['relativize'])
    except Exception, e:
        return (False, "Can not open zone file.")
    has_changed = wzone.delRecord(data['type'], data['name'])
    if has_changed:
        if data['updateserial']:
            wzone.increaseSOASerial()
        wzone.save()
    return (has_changed, wzone.getRecords())

def main():
    fields = {
        "file": {"required": True, "type": "path"},
        "domain": {"required": True, "type": "str"},
        "type": {
            "default": "A",
            "choices": ["NS", "A", "AAAA", "MX", "CNAME", "TXT"],
            "type": "str"
        },
        "name": {"required": True, "type": "str"},
        "data": {"required": False, "type": "str", "default": ""},
        "ttl": {"required": False, "type": "str", "default": "86400"},
        "relativize": {"required": False, "type": "bool", "default": True},
        "updateserial": {"required": False, "type": "bool", "default": True},
        "state": {
            "default": "present",
            "choices": ['present', 'absent'],
            "type": 'str'
        },
    }
    choice_map = {
      "present": state_present,
      "absent": state_absent,
    }
    module = AnsibleModule(argument_spec=fields)

    if not HAS_DNSPYTHON:
        module.fail_json(msg='dnspython is required for this module')

    has_changed, result = choice_map.get(module.params['state'])(module.params)
    module.exit_json(changed=has_changed, meta=result)

if __name__ == '__main__':
    main()