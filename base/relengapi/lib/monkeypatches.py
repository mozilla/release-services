# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


def monkeypatch_Blueprint_root_widget():
    # add a root_widget decorator to Blueprint
    from flask import Blueprint

    def root_widget_template(self, template, priority=0, condition=None):
        if not self.root_widget_templates:
            self.root_widget_templates = []
        self.root_widget_templates.append((priority, template, condition))
    Blueprint.root_widget_template = root_widget_template
    Blueprint.root_widget_templates = None


def monkeypatch():
    monkeypatch_Blueprint_root_widget()
