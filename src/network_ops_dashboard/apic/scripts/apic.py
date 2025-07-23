import requests
import json

# Obtain APIC Cookie
def apicCookie(hostname, username, password):
    headers = {'Content-Type': 'application/json'}
    payload = {'aaaUser': {'attributes': {'name': username, 'pwd': password}}}
    r = requests.post(f'https://{hostname}/api/aaaLogin.json', headers=headers, data=json.dumps(payload), verify=False)
    token = r.json()['imdata'][0]['aaaLogin']['attributes']['token']
    return f'{token}'

# Modify Interface Profile Group for a list of Interface Profiles/Selectors
def apicChangePG(hostname, username, password, intList):
    aci_token = apicCookie(hostname, username, password)
    headers = {'Content-Type': 'application/json', 'Cookie': f'APIC-Cookie='+aci_token}
    try:
        payload = {
        'infraHPortS': {
            'attributes': {
                'dn': f'uni/infra/accportprof-{intList[0]}/hports-{intList[1]}-typ-range', 
                'name': f'{intList[1]}',
                'rn': f'hports-{intList[1]}-typ-range',
                'status': 'created,modified'
                },
                'children': [
                    {
                        'infraRsAccBaseGrp': {
                            'attributes': {
                                'tDn': f'uni/infra/funcprof/accportgrp-{intList[2]}',
                                'status': 'created,modified'
                            },
                            'children': []
                        }
                    }
                ]
            }
        }
        requests.post(f'https://{hostname}/api/node/mo/uni/infra/accportprof-{intList[0]}/hports-{intList[1]}-typ-range.json', headers=headers, data=json.dumps(payload), verify=False)
        print (f'{intList[0]} modified.')
    except Exception as e:
        print (f'Exception modifying {intList[0]}. ({e})')