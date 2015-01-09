# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import docutils.nodes
import fnmatch
import re
import sys
import wsme
import wsme.api
import wsme.rest.args
import wsme.rest.json
import wsme.types

from docutils.statemachine import ViewList
from flask import current_app
from sphinx import addnodes
from sphinx.directives import ObjectDescription
from sphinx.domains import Domain
from sphinx.pycode import ModuleAnalyzer
from sphinx.roles import XRefRole
from sphinx.util import console
from sphinx.util.compat import Directive
from sphinx.util.docfields import Field
from sphinx.util.docfields import GroupedField
from sphinx.util.docfields import TypedField
from sphinx.util.nodes import make_refnode

# Note that this file is not subject to coverage.  This code is only used in
# the documentation-generation process, and not directly tested, aside from
# being run while generating documentation.  In normal circumstances, that does
# not exercise all of the code here, especially error-handling code.


def typename(datatype):
    if hasattr(datatype, '_name'):
        return datatype._name
    else:
        return datatype.__name__


def typereference(datatype):
    if isinstance(datatype, wsme.types.UserType):
        return datatype.name
    elif isinstance(datatype, wsme.types.DictType):
        if datatype.key_type is unicode:
            return '{"...": %s}' % (typereference(datatype.value_type),)
        return '{%s: %s}' % (typereference(datatype.key_type),
                             typereference(datatype.value_type))
    elif isinstance(datatype, wsme.types.ArrayType):
        return '[%s]' % typereference(datatype.item_type)
    elif wsme.types.iscomplex(datatype):
        return ':api:type:`%s`' % (typename(datatype),)
    else:
        return datatype.__name__


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


class TypeDirective(ObjectDescription):

    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = False
    has_content = True
    option_spec = {}

    doc_field_types = [
        TypedField('key', label='Keys',
                   names=('key',), typenames=('keytype',))
    ]

    def get_signatures(self):
        self.type_name = self.arguments[0]
        return [self.type_name]

    def handle_signature(self, sig, signode):
        signode += addnodes.desc_annotation('REST type ', 'REST type ')
        signode += addnodes.desc_name(sig, sig)

    def add_target_and_index(self, name, sig, signode):
        targetname = 'type-' + self.type_name

        # record the target for later cross-referencing
        targets = self.env.domaindata['api']['targets'].setdefault('type', {})
        targets[self.type_name] = self.env.docname, targetname

        # record that we've documented the type
        self.env.domaindata['api']['types'].add(self.type_name)

        # add a target node at the beginning of the result
        signode.insert(0, docutils.nodes.target('', '', ids=[targetname]))


class EndpointDirective(ObjectDescription):

    required_arguments = 3
    optional_arguments = sys.maxint
    final_argument_whitespace = False
    has_content = True
    option_spec = {}

    doc_field_types = [
        GroupedField('param', label='Parameters',
                     names=('param',)),
        Field('response', label='Response Body', has_arg=False,
              names=('response',)),
        Field('body', label='Request Body', has_arg=False,
              names=('body',)),
    ]

    def get_signatures(self):
        self.endpoint_name = self.arguments.pop(0)
        if len(self.arguments) % 2 != 0:
            raise RuntimeError("api:endpoint expects an odd number of arguments "
                               "(endpoint method path method path ..)")
        rv = []
        while self.arguments:
            methods, path = self.arguments[:2]
            self.arguments = self.arguments[2:]
            rv.append((methods, path))
        return rv

    def handle_signature(self, sig, signode):
        methods, path = sig
        signode += addnodes.desc_annotation('endpoint ', 'endpoint ')
        signode += addnodes.desc_addname(methods + ' ', methods + ' ')
        signode += addnodes.desc_name(path, path)

    def add_target_and_index(self, name, sig, signode):
        targetname = 'endpoint-' + self.endpoint_name
        domaindata = self.state.document.settings.env.domaindata
        targets = domaindata['api']['targets'].setdefault('endpoint', {})
        targets[
            self.endpoint_name] = self.state.document.settings.env.docname, targetname

        # record that we've documented the type
        self.env.domaindata['api']['endpoints'].add(self.endpoint_name)

        # add a target node at the beginning of the result
        target_node = docutils.nodes.target('', '', ids=[targetname])
        signode.insert(0, target_node)


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
                raise RuntimeError('no endpoints found matching %s' % (arg,))

        # sort by the first rule of each endpoint
        to_document = sorted(
            to_document, key=lambda t: (t[2][0].rule, t[2][0].methods))

        for endpoint, func, rules in to_document:
            content.append(u'.. api:endpoint:: %s' % endpoint, src)
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
                    argdesc += u':param %s: ' % (arg.name,)
                else:
                    argdesc += u':body: '
                argdesc += typereference(arg.datatype)
                if not arg.mandatory:
                    argdesc += u' - *optional*'
                if arg.default:
                    argdesc += u' - *default*: %r' % (arg.default,)
                content.append(argdesc, src)
            if funcdef.return_type:
                content.append(u'    :response: %s' %
                               typereference(funcdef.return_type), src)
            content.append(u'    ', src)
            if func.__apidoc__:
                for l in trim_docstring(func.__apidoc__).split('\n'):
                    content.append(u'    ' + l, src)
                content.append(u'    ', src)
        self.state.nested_parse(content, 0, node)
        return node.children


class AutoTypeDirective(Directive):

    has_content = True
    required_arguments = 1
    optional_arguments = sys.maxint
    final_argument_whitespace = False
    option_spec = {}

    def get_type_by_name(self, name):
        for ct in wsme.types.registry.complex_types:
            if ct.__name__ == name or (hasattr(ct, '_name') and ct._name == name):
                return ct
        raise RuntimeError("no type named %r" % (name,))

    def get_attr_docs(self, ty):
        # this reaches into some undocumented stuff in sphinx to
        # extract the attribute documentation.
        analyzer = ModuleAnalyzer.for_module(ty.__module__)
        module_attrs = analyzer.find_attr_docs()  # (scope is broken!)
        return {k[1]: v[0] for k, v in module_attrs.iteritems()}

    def run(self):
        src = '<autotype>'

        node = docutils.nodes.paragraph()
        node.document = self.state.document
        if self.content:
            self.state.nested_parse(self.content, 0, node)

        content = ViewList()

        for arg in self.arguments:
            ty = self.get_type_by_name(arg)

            content.append(u'.. api:type:: %s' % arg, src)
            content.append(u'', src)

            if ty.__doc__:
                for l in trim_docstring(ty.__doc__).split('\n'):
                    content.append(u'    ' + l, src)
                content.append(u'    ', src)

            attr_docs = self.get_attr_docs(ty)
            attrs = wsme.types.list_attributes(ty)
            wsme.types.sort_attributes(ty, attrs)
            for attr in attrs:
                content.append(u'    :key %s:' % (attr.name,), src)
                if attr.name in attr_docs:
                    for l in attr_docs[attr.name].split('\n'):
                        content.append(u'        ' + l, src)
                content.append(u'    :keytype %s: %s' % (attr.name,
                                                         typereference(attr.datatype)),
                               src)
            content.append(u'', src)

        self.state.nested_parse(content, 0, node)
        return node.children


class ApiDomain(Domain):
    name = 'api'
    label = 'API'

    directives = {
        'type': TypeDirective,
        'endpoint': EndpointDirective,
        'autoendpoint': AutoEndpointDirective,
        'autotype': AutoTypeDirective,
    }

    roles = {
        'type': XRefRole(),
        'endpoint': XRefRole(),
    }

    initial_data = {
        'types': set(),
        'endpoints': set(),
        'targets': {},
    }

    def resolve_xref(self, env, fromdocname, builder, typ, target, node, contnode):
        targets = self.data['targets'].get(typ, {})
        try:
            todocname, targetname = targets[target]
        except KeyError:
            raise RuntimeError("MISSING REFERENCE: api:%s:%s" % (typ, target))

        return make_refnode(builder, fromdocname,
                            todocname, targetname,
                            contnode, target)


def verify_everything_documented(app, exception):
    if exception:
        return

    bad = False
    app.info(console.white(
        "checking that all REST API types are included in the documentation"))
    documented_types = app.env.domaindata['api']['types']
    for ty in wsme.types.Base.__subclasses__():
        if not ty.__module__.startswith('relengapi.') or '.test_' in ty.__module__:
            continue
        tyname = typename(ty)
        if tyname not in documented_types:
            app.warn(console.red("Type '%s' is not documented" % (tyname,)))
            bad = True

    app.info(console.white(
        "checking that all API endpoints are included in the documentation"))
    all_endpoints = set(ep for ep, func in current_app.view_functions.items()
                        if hasattr(func, '__apidoc__'))
    documented_endpoints = app.env.domaindata['api']['endpoints']
    for undoc in all_endpoints - documented_endpoints:
        app.warn(console.red("Endpoint '%s' is not documented" % (undoc,)))
        bad = True

    if bad:
        raise RuntimeError("missing API documentation")


def setup(app):
    app.add_domain(ApiDomain)
    app.connect('build-finished', verify_everything_documented)
