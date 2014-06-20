# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from docutils.statemachine import ViewList
from flask import current_app
from sphinx.domains import Domain
from sphinx import addnodes
from sphinx.util.compat import Directive
from sphinx.util.docfields import Field
import docutils.nodes
import fnmatch
import re
import sys
import wsme
import wsme.api
import wsme.rest.args
import wsme.rest.json
import wsme.types


class EndpointDirective(Directive):

    required_arguments = 2
    has_content = True
    optional_arguments = sys.maxint
    final_argument_whitespace = False
    option_spec = {}

    doc_field_types = [
        Field('parameter', label='Parameters',
              names=('param', 'parameter', 'arg', 'argument',
                     'keyword', 'kwarg', 'kwparam')),
        Field('returnvalue', label='Returns', has_arg=False,
              names=('returns', 'return')),
        Field('body', label='Body', has_arg=False,
              names=('returns', 'return')),
    ]

    def make_sig(self, methods, path):
        signode = addnodes.desc_signature(path, '')
        signode += addnodes.desc_annotation('endpoint ', 'endpoint ')
        signode += addnodes.desc_addname(methods + ' ', methods + ' ')
        signode += addnodes.desc_name(path, path)
        return signode

    def run(self):
        if len(self.arguments) % 2 != 0:
            raise self.error("api:endpoint expects an even number of arguments "
                             "(method path method path ..)")
        node = addnodes.desc()
        node.document = self.state.document
        node['objtype'] = node['desctype'] = 'endpoint'
        while self.arguments:
            methods, path = self.arguments[:2]
            self.arguments = self.arguments[2:]
            node.append(self.make_sig(methods, path))
        contentnode = addnodes.desc_content()
        self.state.nested_parse(self.content, self.content_offset, contentnode)
        node.append(contentnode)
        return [node]


# from PEP-0257
def trim_docstring(docstring):
    if not docstring:
        return ''
    # Convert tabs to spaces (following the normal Python rules)
    # and split into a list of lines:
    lines = docstring.expandtabs().splitlines()
    # Determine minimum indentation (first line doesn't count):
    indent = sys.maxint
    for line in lines[1:]:
        stripped = line.lstrip()
        if stripped:
            indent = min(indent, len(line) - len(stripped))
    # Remove indentation (first line is special):
    trimmed = [lines[0].strip()]
    if indent < sys.maxint:
        for line in lines[1:]:
            trimmed.append(line[indent:].rstrip())
    # Strip off trailing and leading blank lines:
    while trimmed and not trimmed[-1]:
        trimmed.pop()
    while trimmed and not trimmed[0]:
        trimmed.pop(0)
    # Return a single string:
    return '\n'.join(trimmed)


# modified, from
# https://github.com/stackforge/wsme/blob/master/wsmeext/sphinxext.py
def datatypename(datatype):
    if isinstance(datatype, wsme.types.UserType):
        return datatype.name
    if isinstance(datatype, wsme.types.DictType):
        return 'dict(%s: %s)' % (datatypename(datatype.key_type),
                                 datatypename(datatype.value_type))
    if isinstance(datatype, wsme.types.ArrayType):
        return 'list(%s)' % datatypename(datatype.item_type)
    if hasattr(datatype, '_name'):
        return datatype._name
    return datatype.__name__


class AutoEndpointDirective(Directive):

    has_content = True
    required_arguments = 0
    optional_arguments = sys.maxint
    final_argument_whitespace = False
    option_spec = {}

    def get_rules_by_endpoint(self):
        rules_by_endpoint = {}
        for rule in current_app.url_map.iter_rules():
            rules_by_endpoint.setdefault(rule.endpoint, []).append(rule)
        return rules_by_endpoint

    def run(self):
        src = '<autoendpoint>'
        rules_by_endpoint = self.get_rules_by_endpoint()

        node = docutils.nodes.paragraph()
        node.document = self.state.document
        if self.content:
            self.state.nested_parse(self.content, 0, node)

        content = ViewList()

        to_document = set()
        for arg in self.arguments or ['*']:
            found = False
            endpoint_re = re.compile(fnmatch.translate(arg))
            # generate a list of strings, including endpoint directives, that will
            # be parsed to generate the final output.
            for endpoint, func in current_app.view_functions.items():
                if not hasattr(func, '__apidoc__'):
                    continue
                if not endpoint_re.match(endpoint):
                    continue

                rules = rules_by_endpoint[endpoint]
                to_document.add((endpoint, func, tuple(rules)))
                found = True
            if not found:
                raise self.error('no endpoints found matching %s' % (arg,))

        # sort by the first rule of each endpoint
        to_document = sorted(
            to_document, key=lambda t: (t[2][0].rule, t[2][0].methods))

        for endpoint, func, rules in to_document:
            content.append(u'.. api:endpoint::', src)
            for rule in sorted(rules, key=lambda r: r.rule):
                methods = [
                    m for m in rule.methods if m not in ('HEAD', 'OPTIONS')]
                content.append(u'    %s %s' %
                               ('|'.join(sorted(methods)), rule.rule), src)
            content.append(u'', src)

            funcdef = wsme.api.FunctionDefinition.get(func)
            for arg in funcdef.arguments:
                argdesc = u'    '
                if arg.name != 'body':
                    argdesc += u':parameter %s: ' % (arg.name,)
                else:
                    argdesc += u':body: '
                argdesc += datatypename(arg.datatype)
                if not arg.mandatory:
                    argdesc += u' - *optional*'
                if arg.default:
                    argdesc += u' - *default*: %r' % (arg.default,)
                content.append(argdesc, src)
            if funcdef.return_type:
                content.append(u'    :returns: %s' %
                               datatypename(funcdef.return_type), src)
            content.append(u'    ', src)
            if func.__apidoc__:
                for l in trim_docstring(func.__apidoc__).split('\n'):
                    content.append(u'    ' + l, src)
                content.append(u'    ', src)
        self.state.nested_parse(content, 0, node)
        return node.children

# TODO: document permissions
# TODO: document types
# TODO: xrefs
# TODO: catch undocumented apimethods in tests


class ApiDomain(Domain):
    name = 'api'
    label = 'API'

    directives = {
        'endpoint': EndpointDirective,
        'autoendpoint': AutoEndpointDirective,
    }

    roles = {
    }

    initial_data = {
    }


# initialize the Sphinx app
def setup(app):
    app.add_domain(ApiDomain)
