"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: MIT-0
"""
import re
from cfnlint.rules import CloudFormationLintRule
from cfnlint.rules import RuleMatch


class Sid(CloudFormationLintRule):
    """Check if IAM Policy Sid is correct"""
    id = 'W2512'
    shortdesc = 'Check IAM Resource Policies Sid syntax'
    description = 'See if the elements inside an IAM Resource policy are configured correctly.'
    source_url = 'https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_grammar.html'
    tags = ['properties', 'iam']

    def __init__(self):
        """Init"""
        super(Sid, self).__init__()
        self.idp_and_keys = {
            'AWS::IAM::Group': 'Policies',
            'AWS::IAM::ManagedPolicy': 'PolicyDocument',
            'AWS::IAM::Policy': 'PolicyDocument',
            'AWS::IAM::Role': 'Policies',
            'AWS::IAM::User': 'Policies',
        }
        for resource_type in self.idp_and_keys:
            self.resource_property_types.append(resource_type)
        self.sid_regex = re.compile('^[A-Za-z0-9]*$')

    def check_policy_document(self, value, path):
        """Check policy document"""
        sids = [] # sids must be unique
        matches = []

        if not isinstance(value, dict):
            return matches

        for e_v, e_p in value.items_safe(path[:]):
            for p_vs, p_p in e_v.items_safe(e_p[:]):
                statements = p_vs.get('Statement', [])
                if 'get' in dir(statements):
                    statements = [statements]
                for statement in statements:
                    if 'Sid' in statement:
                        sid = statement.get('Sid')
                        if self.sid_regex.search(sid) is None:
                            message = 'basic alphanumeric characters (A-Z,a-z,0-9) are the only allowed characters in the Sid value'
                            matches.append(RuleMatch(p_p + ['Sid'], message))
                        if sid in sids:
                            message = 'IAM Sid values should be unique'
                            matches.append(RuleMatch(p_p + ['Sid'], message))
                        else:
                            sids.append(sid)

        return matches

    def match_resource_properties(self, properties, resourcetype, path, cfn):
        """Check CloudFormation Properties"""
        matches = []

        key = self.idp_and_keys.get(resourcetype)

        if key == 'Policies':
            for index, policy in enumerate(properties.get(key, [])):
                matches.extend(
                    cfn.check_value(
                        obj=policy, key='PolicyDocument',
                        path=path[:] + ['Policies', index],
                        check_value=self.check_policy_document,
                    ))
        else:
            matches.extend(
                cfn.check_value(
                    obj=properties, key=key,
                    path=path[:],
                    check_value=self.check_policy_document
                ))

        return matches