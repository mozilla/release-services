# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import

import click
import os

import please_cli.config


@click.command()
def cmd(app):
    pass
    # TODO
    # update-all: update-tools update-projects
    # update-tools: $(foreach tool, $(TOOLS), update-tool-$(tool))
    # update-projects: $(foreach app, $(PROJECTS), update-app-$(app))
    # 
    # update-app: require-APP update-app-$(APP)
    # update-app-%: tmpdir nix
    # 	nix-shell nix/update.nix --argstr pkg $(subst update-app-,,$@)
    # 
    # 
    # update-tool: require-TOOL update-tool-$(TOOL)
    # update-tool-%: tmpdir nix
    # 	nix-shell nix/update.nix --argstr pkg tools.$(subst update-tool-,,$@)


if __name__ == "__main__":
    cmd()
