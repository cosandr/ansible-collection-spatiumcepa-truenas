from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible_collections.spatiumcepa.truenas.plugins.module_utils.common import HTTPCode, HTTPResponse, \
    TruenasServerError, TruenasModelError, TruenasUnexpectedResponse
from ansible_collections.spatiumcepa.truenas.plugins.module_utils.resources import TruenasJailFstab
from ansible.module_utils.connection import Connection
from ansible.module_utils.basic import AnsibleModule


ANSIBLE_METADATA = {
    "metadata_version": "1.1",
    "status": ["preview"],
    "supported_by": "community"
}

DOCUMENTATION = """
module: truenas_api_jail_fstab

short_description: Manage TrueNAS jail fstab entries

description:
  - Manage TrueNAS jail fstab entries via REST API

version_added: "0.2"

author: Andrei Costescu (@cosandr)

options:
  state:
    type: str
    description: Desired state of the jail fstab entry
    default: fetch
    choices: [ absent, present, fetch ]
  jail:
    type: str
    description: Name of the jail to operate on
    required: true
  source:
    type: str
    description: Source of mount on the host
  destination:
    type: str
    description: Destination of mount, must be full path
  fsoptions:
    type: str
    description: Filesystem options
    default: rw
    choices: [ rw, ro ]
  force:
    type: bool
    description: Replace entry if source is the same
    default: false
"""

EXAMPLES = """
  - name: Create jail share
    spatiumcepa.truenas.truenas_api_jail_fstab:
      state: present
      jail: "ansible-test"
      source: "/mnt/tank"
      destination: "/mnt/ssd/iocage/jails/ansible-test/root/mnt/tank"
"""

RETURN = """
response:
  description: HTTP response returned from the API call
  returned: success
  type: dict
"""


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state={'type': 'str', 'choices': ['absent', 'present', 'fetch'], 'default': 'fetch'},
            jail={'type': 'str', 'required': True},
            source={'type': 'str'},
            destination={'type': 'str'},
            fsoptions={'type': 'str', 'choices': ['ro', 'rw'], 'default': 'rw'},
            force={'type': 'bool', 'default': False},
        ),
        supports_check_mode=True,
    )

    connection = Connection(module._socket_path)
    user_resource = TruenasJailFstab(connection, module.check_mode)

    try:
        response = None
        state_param = module.params['state']
        jail_param = module.params['jail']
        source = module.params['source']
        destination = module.params['destination']
        fsoptions = module.params['fsoptions']
        force = module.params['force']

        if state_param == 'present':
            if not destination or not source:
              module.fail_json(msg='Source and destination are required') 
            response = user_resource.update_item(jail_param, source, destination, fsoptions, force)
            failed = response[HTTPResponse.STATUS_CODE] != HTTPCode.OK
        elif state_param == 'absent':
            if not destination:
              module.fail_json(msg='Destination is required') 
            response = user_resource.delete_item(jail_param, source, destination)
            failed = response[HTTPResponse.STATUS_CODE] != HTTPCode.OK
        if state_param == 'fetch':
            response = user_resource.fetch(jail_param)
            failed = response[HTTPResponse.STATUS_CODE] != HTTPCode.OK

        module.exit_json(
            created=user_resource.resource_created,
            changed=user_resource.resource_changed,
            deleted=user_resource.resource_deleted,
            failed=failed,
            response=response,
            source=source,
            destination=destination,
            fsoptions=fsoptions,
        )

    except TruenasServerError as e:
        module.fail_json(msg='Server returned an error, satus code: %s. '
                             'Server response: %s' % (e.code, e.response))

    except TruenasModelError as e:
        module.fail_json(msg='Data model error: %s' % (e.args[0]))

    except TruenasUnexpectedResponse as e:
        module.fail_json(msg=e.args[0])

    except ConnectionError as e:
        module.fail_json(msg=e.args[0])


if __name__ == '__main__':
    main()
