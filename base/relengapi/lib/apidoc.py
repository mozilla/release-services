# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from docutils.statemachine import ViewList
from flask import current_app
from sphinx.domains import Domain
from sphinx.domains.python import PyClasslike, PyClassmember
from sphinx import addnodes
from sphinx.pycode import ModuleAnalyzer
from sphinx.roles import XRefRole
from sphinx.directives import ObjectDescription
from sphinx.util.compat import Directive
from sphinx.util.docfields import Field
from sphinx.util.nodes import make_refnode
import docutils.nodes
import fnmatch
import re
import sys
import wsme
import wsme.api
import wsme.rest.args
import wsme.rest.json
import wsme.types


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


# adapted from wsme
class TypeDirective(PyClasslike):

    def get_index_text(self, modname, name_cls):
        return '%s (REST API type)' % name_cls[0]

    def run(self):
        name = self.arguments[0]
        targetname = 'type-' + name
        result = super(TypeDirective, self).run()
        # record the target for later cross-referencing
        targets = self.env.domaindata['api']['targets'].setdefault('type', {})
        targets[name] = self.env.docname, targetname
        # add a target node at the beginning of the result
        result.insert(0, docutils.nodes.target('', '', ids=[targetname]))
        return result

    def add_target_and_index(self, name_cls, sig, signode):
        ret = super(TypeDirective, self).add_target_and_index(
            name_cls, sig, signode
        )
        name = name_cls[0]
        types = self.env.domaindata['api']['types']
        if name in types:
            self.state_machine.reporter.warning(
                'duplicate type description of %s ' % name)
        types[name] = self.env.docname
        return ret


# adapted from wsme
class AttributeDirective(PyClassmember):
    doc_field_types = [
        Field('datatype', label='Type', has_arg=False,
              names=('type', 'datatype'))
    ]


class EndpointDirective(ObjectDescription):

    required_arguments = 3
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

    def get_signatures(self):
        self.endpoint_name = self.arguments.pop(0)
        if len(self.arguments) % 2 != 0:
            raise self.error("api:endpoint expects an odd number of arguments "
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
        targets[self.endpoint_name] = self.state.document.settings.env.docname, targetname

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
                raise self.error('no endpoints found matching %s' % (arg,))

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


class AutoTypeDirective(Directive):

    has_content = True
    required_arguments = 1
    optional_arguments = sys.maxint
    final_argument_whitespace = False
    option_spec = {}

    def get_type_by_name(self, name):
        for ct in wsme.types.registry.complex_types:
            if datatypename(ct) == name:
                return ct
        raise self.error("no type named %r" % (name,))

    def get_attr_docs(self, ty):
        # this reaches into some undocumented stuff in sphinx to
        # extract the attribute documentation.
        analyzer = ModuleAnalyzer.for_module(ty.__module__)
        module_attrs = analyzer.find_attr_docs(scope=ty.__name__)
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
                content.append(u'    .. api:attribute:: %s' %
                               (attr.name,), src)
                content.append(u'', src)
                content.append(u'        :type: %s' %
                               datatypename(attr.datatype), src)
                content.append(u'', src)
                if attr.name in attr_docs:
                    for l in attr_docs[attr.name].split('\n'):
                        content.append(u'        ' + l, src)

        self.state.nested_parse(content, 0, node)
        return node.children

# TODO: document permissions
# TODO: xrefs
# TODO: catch undocumented apimethods, types in tests


class ApiDomain(Domain):
    name = 'api'
    label = 'API'

    directives = {
        'type': TypeDirective,
        'attribute': AttributeDirective,
        'endpoint': EndpointDirective,
        'autoendpoint': AutoEndpointDirective,
        'autotype': AutoTypeDirective,
    }

    roles = {
        'type': XRefRole(),
        'endpoint': XRefRole(),
    }

    initial_data = {
        'types': {},
        'targets': {},
    }

    def resolve_xref(self, env, fromdocname, builder, typ, target, node, contnode):
        targets = self.data['targets'].get(typ, {})
        try:
            todocname, targetname = targets[target]
        except KeyError:
            raise self.error("MISSING REFERENCE: api:%s:%s" % (typ, target))

        return make_refnode(builder, fromdocname,
                            todocname, targetname,
                            contnode, target)


# initialize the Sphinx app
def setup(app):
    app.add_domain(ApiDomain)
