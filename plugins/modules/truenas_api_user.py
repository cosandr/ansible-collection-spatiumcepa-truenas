from __future__ import absolute_import, division, print_function
from ansible_collections.spatiumcepa.truenas.plugins.module_utils.common import HTTPCode, HTTPResponse, \
    TruenasServerError, TruenasModelError, TruenasUnexpectedResponse
from ansible_collections.spatiumcepa.truenas.plugins.module_utils.resources import TruenasUser
from ansible_collections.spatiumcepa.truenas.plugins.module_utils.arg_specs import API_ARG_SPECS, strip_null_module_params
from ansible.module_utils.connection import Connection, ConnectionError
from ansible.module_utils.basic import AnsibleModule
__metaclass__ = type


ANSIBLE_METADATA = {
    "metadata_version": "1.1",
    "status": ["preview"],
    "supported_by": "community"
}

DOCUMENTATION = """
module: truenas_api_user

short_description: Manage TrueNAS Users

description:
  - Manage TrueNAS Users via REST API

version_added: "2.10"

author: Nicholas Kiraly (@nkiraly)

options:
  state:
    type: str
    description: Desired state of the user
    default: present
    choices: [ absent, present ]
  model:
    type: dict
    description: ''
    options:
      attributes:
        description: ''
        suboptions: {}
        type: dict
      email:
        description: ''
        type: str
      full_name:
        description: ''
        type: str
      group:
        description: ''
        type: int
      groups:
        description: ''
        type: list
      home:
        description: ''
        type: str
      home_mode:
        description: ''
        type: str
      locked:
        description: ''
        type: bool
      microsoft_account:
        description: ''
        type: bool
      password:
        description: ''
        type: str
      password_disabled:
        description: ''
        type: bool
      shell:
        description: ''
        type: str
      smb:
        description: ''
        type: bool
      sshpubkey:
        description: ''
        type: str
      sudo:
        description: ''
        type: bool
      sudo_commands:
        description: ''
        type: list
      sudo_nopasswd:
        description: ''
        type: bool
      uid:
        description: ''
        type: int
      username:
        description: ''
        type: str
"""

EXAMPLES = """
  - name: Manage User via TrueNAS API
    spatiumcepa.truenas.truenas_api_group:
      name: root
      model:
        email: truenas@spatium-cepa.com
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
            model=API_ARG_SPECS[TruenasUser.RESOURCE_API_MODEL],
            state={'type': 'str', 'choices': ['absent', 'present'], 'default': 'present'}
        ),
        supports_check_mode=True,
    )

    connection = Connection(module._socket_path)
    user_resource = TruenasUser(connection, module.check_mode)

    try:
        response = None
        created = False
        model_param = strip_null_module_params(module.params['model'])
        state_param = module.params['state']

        if state_param == 'present':
            find_item_response = user_resource.find_item(model_param)
            if find_item_response[HTTPResponse.STATUS_CODE] == HTTPCode.NOT_FOUND:
                # not found, so create it
                response = user_resource.create(model_param)
                created = True
            else:
                # group_create is in #/components/schemas/user_create_0 but not in #/components/schemas/user_update_1
                update_model = model_param
                popped = update_model.pop("group_create", None)
                found_id = find_item_response[HTTPResponse.BODY][TruenasUser.RESOURCE_ITEM_ID_FIELD]
                response = user_resource.update_item(found_id, model_param)
        elif state_param == 'absent':
            response = user_resource.delete_item(model_param)

        module.exit_json(
            changed=user_resource.resource_changed,
            failed=response[HTTPResponse.STATUS_CODE] != HTTPCode.OK,
            response=response,
            created=created,
            submitted_model=model_param,
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