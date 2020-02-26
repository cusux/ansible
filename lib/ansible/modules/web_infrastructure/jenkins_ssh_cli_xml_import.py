#!/usr/bin/python
# -*- coding: utf-8 -*

# Copyright: (c) 2020, Paul Wetering <pwetering@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: jenkins_ssh_cli_import_xml
author:
  - Paul Wetering (@cusux)
short_description: Import XML Jenkins objects using the SSH CLI
version_added: "2.9"
description:
  - The C(jenkins_ssh_cli_import_xml) module imports XML files utilizing the Jenkins SSH CLI to create Jenkins objects.
options:
  user:
    description:
      - The SSH user to setup the connection with the SSH CLI.
    required: true
  host:
    description:
      - The Jenkins SSH CLI host to connect to. By default this module should be ran on the Jenkins node, therefore it is defaulted to C(localhost).
    default: localhost
  port:
    description:
      - The default Jenkins web interface port. By default Jenkins web interface is set to C(8080).
    default: 8080
  type:
    description:
      - Type of Jenkins object to import.
    choices: [credential, node, job]
    required: true
  credential_store:
    description:
      - The credential store in which to create the credentials object. If this option is used, the C(type=credential) must be specified.
    default: "system::system::jenkins"
  credential_domain:
    description:
      - The credential domain in which to create the credentials object. If this option is used, the C(type=credential) must be specified.
    default: "_"
  xml_code_input:
    description:
      - The XML code input for Jenkins object creation. If this option is used, the C(xml_file_input) must not be used.
  xml_file_input:
    description:
      - The absolute remote XML file path for Jenkins object creation. If this option is used, the C(xml_code_input) must not be used.
notes:
  - Due to the Jenkins SSH CLI design, it does not report on success. It is important to set C(change_when) to clarify module usage in the ansible output.
'''

EXAMPLES = r'''
# Create a new Jenkins credential using a variable containing the Jenkins credential XML code
- name: Create Jenkins credential by XML code input
  jenkins_ssh_cli_import_xml:
    user: '{{ ansible_user }}'
    host: jenkins.example.com
    port: 8181
    type: credential
    credential_store: 'system::system::jenkins'
    credential_domain: 'my_domain'
    xml_code_input: '{{ jenkins_credential_xml_code }}'

# Create a new Jenkins node using a variable containing the remote Jenkins node XML file
- name: Create Jenkins node by XML file input
  jenkins_ssh_cli_import_xml:
    user: '{{ ansible_user }}'
    type: node
    xml_file_input: '{{ jenkins_credential_xml_file }}'
'''

RETURN = r'''
output:
    description: Result of script
    returned: always
    type: str
    sample: 'Import successful'
'''

import subprocess
import json

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url
from ansible.module_utils._text import to_native


def compile_cli_command(cmd, store, domain, xml):
    # command = [credential, node, job]
    # store = credential store
    # domain = credential domain
    # xml = string with XML contents or string with XML file location

    # IF xml_type is code, we must stream it to remote file.
    # IF xml_type is local file, we must copy local file to remote file.
    # IF xml_type is remote file, just import the fucker.

    if 'credential' in cmd:
        command = 'create-credentials-by-xml' + store + domain + '<' + xml
        return('credential')
    elif 'node' in cmd:
        command = 'create-node < ' + xml
        return('node')
    elif 'job' in cmd:
        command = 'create-job < ' + xml
        return('job')

    result = command
    return result


def flatten_xml(xml):
    test = 1234
    # gets string or multiline
    # result is flattened string
    return()


def process_command(module, user, host, port, cmd_type, store, domain, xml_type, xml):
    resp, info = fetch_url(module,
                           url="http://" + host + ":" + str(port) + "/login",
                           method="GET")

    if info["status"] != 200:
        module.fail_json(msg="HTTP error " + str(info["status"]) + " " + info["msg"], output='')

    port = info['x-ssh-endpoint'].split(':')[1]

    # if 'code' in xml_type:
    #     return()
    # elif 'file' in xml_type:
    #     return()

    ssh_command = compile_cli_command(cmd_type, store, domain, xml)

    # subprocess.Popen("ssh -l {user} -p {port} {host} {cmd}".format(user=user, port=port, host=host, cmd='ls -l'),
    #                  shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    # return(port)
    return(ssh_command)

def main():
    module = AnsibleModule(
        argument_spec=dict(user=dict(type="str", required=True),
                           host=dict(type="str", required=False, default="localhost"),
                           port=dict(type="int", required=False, default=8080),
                           type=dict(choices=['credential', 'node', 'job'], required=True),
                           credential_store=dict(type="str", required=False, default="system::system::jenkins"),
                           credential_domain=dict(type="str", required=False, default="_"),
                           xml_code_input=dict(type="str", required=False),
                           xml_file_input=dict(type="str", required=False))
    )

    ssh_user = module.params['user']
    ssh_host = module.params['host']
    ssh_port = module.params['port']
    object_type = module.params['type']
    cred_store = module.params['credential_store']
    cred_domain = module.params['credential_domain']
    result = None

    if module.params['xml_code_input'] is not None and module.params['xml_file_input'] is None:
        object_xml_type = 'code'
        object_xml = module.params['xml_code_input']
    elif module.params['xml_file_input'] is not None and module.params['xml_code_input'] is None:
        object_xml_type = 'file'
        object_xml = module.params['xml_file_input']
    else:
        result = "Exception: specify either 'xml_code_input' or 'xml_file_input' arguments."

    if result is not None:
        if 'Exception:' in result:
            module.fail_json(msg="script failed with message:\n " + result, output='')
    elif result is None:
        result = process_command(module, ssh_user, ssh_host, ssh_port, object_type, cred_store, cred_domain, object_xml_type, object_xml)

    module.exit_json(
        output=result,
    )


if __name__ == '__main__':
    main()
