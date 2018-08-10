import React from 'react';
import {
  ButtonToolbar, Button, FormGroup, FormControl, ControlLabel, InputGroup, DropdownButton,
  MenuItem, Collapse, Modal,
} from 'react-bootstrap';
import { object } from 'prop-types';
import { NavLink } from 'react-router-dom';

import config from '../../config';
import { getBuildNumbers, getShippedReleases } from '../../components/api';
import { getPushes, getVersion, getLocales } from '../../components/mercurial';
import maybeShorten from '../../components/text';

export default class NewRelease extends React.Component {
  static contextTypes = {
    authController: object.isRequired,
  };

  constructor(...args) {
    super(...args);
    this.state = Object.assign(this.defaultState());
  }

  set version(version) {
    this.setState({
      version,
    });
  }

  defaultState = () => ({
    selectedProduct: {},
    selectedBranch: {},
    suggestedRevisions: [],
    revision: '',
    version: '',
    buildNumber: 0,
    partialVersions: [],
    showModal: false,
    errorMsg: null,
    submitted: false,
    inProgress: false,
  });

  readyToSubmit = () => (
    this.state.version !== '' &&
    this.state.buildNumber > 0 &&
    (this.state.selectedProduct.enablePartials ?
      this.state.partialVersions.length > 0 : true)
  );

  open = () => {
    this.setState({ showModal: true });
  };

  close = () => {
    this.setState(Object.assign(this.defaultState()));
  };

  handleBranch = async (branch) => {
    this.setState({
      selectedBranch: branch,
      revision: '',
      version: '',
      buildNumber: 0,
      partialVersions: [],
    });
    const pushes = await getPushes(branch.repo);
    const suggestedRevisions = Object.values(pushes.pushes).map(push =>
      ({ ...push.changesets[0], date: new Date(push.date * 1000) })).reverse().filter(push =>
      push.desc.indexOf('DONTBUILD') === -1);
    this.setState({ suggestedRevisions });
  };

  guessBuildId = async () => {
    const buildNumbers = await getBuildNumbers(
      this.state.selectedProduct.product,
      this.state.selectedBranch.branch,
      this.state.version,
    );
    const nextBuildNumber = buildNumbers.length !== 0 ? Math.max(...buildNumbers) + 1 : 1;
    this.setState({
      buildNumber: nextBuildNumber,
    });
  };

  guessPartialVersions = async () => {
    const { product } = this.state.selectedProduct;
    const { branch } = this.state.selectedBranch;
    const shippedReleases = await getShippedReleases(product, branch);
    const shippedBuilds = shippedReleases.map(r => `${r.version}build${r.build_number}`);
    // take first N releases
    const suggestedBuilds = shippedBuilds.slice(0, 3);

    this.setState({
      partialVersions: suggestedBuilds,
    });
  }

  handleSuggestedRev = async (rev) => {
    this.setState({
      revision: rev.node,
    });
    this.version = await getVersion(
      this.state.selectedBranch.repo, rev.node,
      this.state.selectedProduct.appName,
    );
    await this.guessBuildId();
    if (this.state.selectedProduct.enablePartials) {
      await this.guessPartialVersions();
    }
  };

  handleProduct = (product) => {
    this.setState({
      selectedProduct: product,
      selectedBranch: {},
      suggestedRevisions: [],
      revision: '',
      version: '',
      buildNumber: 0,
      partialVersions: [],
    });
  };

  handleRevisionChange = async (event) => {
    this.setState({
      revision: event.target.value,
    });
    this.version = await getVersion(this.state.selectedBranch.repo, event.target.value);
    await this.guessBuildId();
  };

  handlePartialsChange = async (event) => {
    this.setState({
      partialVersions: event.target.value.split(',').map(v => v.trim()),
    });
  };

  submitRelease = async () => {
    this.setState({ inProgress: true });
    const { product } = this.state.selectedProduct;
    const { branch } = this.state.selectedBranch;
    const releaseObj = {
      product,
      branch,
      revision: this.state.revision,
      version: this.state.version,
      build_number: this.state.buildNumber,
      release_eta: '', // TODO
    };

    if (this.state.selectedProduct.enablePartials) {
      const partialUpdates = await Promise.all(this.state.partialVersions.map(async (ver) => {
        const [version, buildNumber] = ver.split('build');
        const shippedReleases = await getShippedReleases(product, branch, version, buildNumber);
        if (shippedReleases.length !== 1) {
          this.setState({
            inProgress: false,
            errorMsg: `More than one release entries for ${product} ${branch} ${version} build ${buildNumber}`,
          });
          return null;
        }
        const { revision } = shippedReleases[0];
        const locales = await getLocales(
          this.state.selectedBranch.repo, revision,
          this.state.selectedProduct.appName,
        );
        return [
          version, { buildNumber, locales },
        ];
      }));
      const partialUpdatesFlattened = {};
      partialUpdates.forEach(([v, e]) => {
        partialUpdatesFlattened[v] = e;
      });
      releaseObj.partial_updates = partialUpdatesFlattened;
    }
    await this.doEet(releaseObj);
    this.setState({ inProgress: false });
  };

  doEet = async (releaseObj) => {
    if (!this.context.authController.userSession) {
      this.setState({ errorMsg: 'Login required!' });
      return;
    }
    const url = `${config.API_URL}/releases`;
    const { accessToken } = this.context.authController.getUserSession();
    const headers = {
      Authorization: `Bearer ${accessToken}`,
      'Content-Type': 'application/json',
    };
    try {
      const body = JSON.stringify(releaseObj);
      const response = await fetch(url, { method: 'POST', headers, body });
      if (!response.ok) {
        this.setState({ errorMsg: 'Auth failure!' });
        return;
      }
      this.setState({ submitted: true });
    } catch (e) {
      this.setState({ errorMsg: 'Server issues!' });
      throw e;
    }
  };

  renderBody = () => {
    const { inProgress, submitted, errorMsg } = this.state;
    if (errorMsg) {
      return (
        <div>
          <p>{errorMsg}</p>
        </div>
      );
    }
    if (inProgress) {
      return (
        <div>
          <h4>Working....</h4>
        </div>
      );
    }
    if (!submitted) {
      const url = `${config.TREEHERDER_URL}/#/jobs?repo=${this.state.selectedBranch.project}&revision=${this.state.revision}`;
      const buildName =
        `${this.state.selectedProduct.product}-${this.state.version}-build${this.state.buildNumber}`;
      return (
        <div>
          <h4>The following release will be submitted:</h4>
          <div>
            <a href={url}>{buildName}</a>
          </div>
        </div>
      );
    }
    return (
      <div>
        Done. Start the release from <NavLink to="/">the list of releases</NavLink>
      </div>
    );
  };


  renderPartials = () => {
    const { selectedProduct, partialVersions } = this.state;
    if (selectedProduct && selectedProduct.enablePartials) {
      return (
        <div>
          <div className="text-muted">Partial versions:</div>
          <FormControl
            type="text"
            value={partialVersions.join(',')}
            onChange={this.handlePartialsChange}
          />
          <small>
            Coma-separated list of versions with build number, e.g. 59.0b8build7.
            UX will be improved!
          </small>
        </div>
      );
    }
    return '';
  };

  render() {
    return (
      <div className="container">
        <h3>Start a new release</h3>
        <div>
          <ButtonToolbar>
            {config.PRODUCTS.map(product => (
              <Button
                key={product.product}
                bsStyle={this.state.selectedProduct === product ? 'primary' : 'default'}
                bsSize="large"
                onClick={() => this.handleProduct(product)}
              >
                {product.prettyName}
              </Button>
            ))}
          </ButtonToolbar>
        </div>
        <Collapse in={this.state.selectedProduct.branches
                && this.state.selectedProduct.branches.length > 0}
        >
          <div style={{ paddingTop: '10px', paddingBottom: '10px' }}>
            <ButtonToolbar>
              {this.state.selectedProduct.branches &&
               this.state.selectedProduct.branches.map(branch => (
                 <Button
                   key={branch.project}
                   bsStyle={this.state.selectedBranch === branch ? 'primary' : 'default'}
                   bsSize="large"
                   onClick={() => this.handleBranch(branch)}
                 >
                   {branch.prettyName}
                 </Button>
              ))}
            </ButtonToolbar>
          </div>
        </Collapse>
        <Collapse in={this.state.selectedBranch.repo && this.state.selectedBranch.repo.length > 0}>
          <div>
            <FormGroup>
              <ControlLabel>Revision</ControlLabel>
              <InputGroup>
                <DropdownButton
                  componentClass={InputGroup.Button}
                  id="input-dropdown-addon"
                  title="Suggested revisions"
                >
                  {this.state.suggestedRevisions && this.state.suggestedRevisions.map(rev => (
                    <MenuItem
                      onClick={() => this.handleSuggestedRev(rev)}
                      key={rev.node}
                      title={
                        `${rev.date.toString()} - ${rev.node} - ${rev.desc}`
                      }
                    >
                      {rev.date.toDateString()}
                      {' '} - {' '}
                      {rev.node.substring(0, 8)}
                      {' '} - {' '}
                      {maybeShorten(rev.desc)}
                    </MenuItem>
                  ))}
                </DropdownButton>
                <FormControl type="text" value={this.state.revision} onChange={this.handleRevisionChange} />
              </InputGroup>
            </FormGroup>
            <div className="text-muted">Version: {this.state.version || ''}</div>
            <div className="text-muted">Build number: {this.state.buildNumber || ''}</div>
            {this.renderPartials()}
            <div style={{ paddingTop: '10px', paddingBottom: '10px' }}>
              <Button type="submit" bsStyle="primary" onClick={this.open} disabled={!this.readyToSubmit()}>Start tracking it!</Button>
              <Modal show={this.state.showModal} onHide={this.close}>
                <Modal.Header closeButton>
                  <Modal.Title>Start release</Modal.Title>
                </Modal.Header>
                <Modal.Body>
                  {this.renderBody()}
                </Modal.Body>
                <Modal.Footer>
                  <Collapse in={!this.state.submitted}>
                    <div>
                      <Button
                        onClick={this.submitRelease}
                        bsStyle="danger"
                        disabled={!this.context.authController.userSession || this.state.inProgress}
                      >
                        Do eet!
                      </Button>
                      <Button onClick={this.close} bsStyle="primary">Close</Button>
                    </div>
                  </Collapse>
                </Modal.Footer>
              </Modal>
            </div>
          </div>
        </Collapse>

      </div>
    );
  }
}
