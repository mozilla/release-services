import React from 'react';
import { ProgressBar, Button, Modal, Collapse } from 'react-bootstrap';
import { object } from 'prop-types';
import ReactInterval from 'react-interval';
import { Queue } from 'taskcluster-client-web';
import config from '../../config';

const statusStyles = {
  // TC statuses
  unscheduled: 'info',
  pending: 'info',
  running: 'info',
  completed: 'success',
  failed: 'danger',
  exception: 'warning',
  // Additional statuses
  ready: 'info',
  blocked: 'info',
};

const taskStatus = async (taskId) => {
  const status = await (new Queue()).status(taskId);
  return status;
};

export default class ListReleases extends React.Component {
  constructor(...args) {
    super(...args);
    this.state = {
      loaded: false,
      message: '',
      releases: [],
    };
  }

  async componentDidMount() {
    await this.getReleases();
  }

  getReleases = async () => {
    try {
      const req = await fetch(`${config.API_URL}/releases`);
      const releases = await req.json();
      let message = '';
      if (releases.length === 0) {
        message = <h3>No pending releases!</h3>;
      }
      this.setState({
        releases,
        message,
        loaded: true,
      });
    } catch (e) {
      const message = <h3>Failed to fetch releases!</h3>;
      this.setState({
        loaded: true,
        message,
        releases: [],
      });
      throw e;
    }
  };

  render() {
    const { releases, loaded, message } = this.state;
    return (
      <div className="container">
        <h3>Releases in progress</h3>
        <div>
          {loaded || <b>loading...</b>}
          {message}
          {releases.length > 0 && releases.map(release => (
            <Release
              release={release}
              key={release.name}
            />))}
          <ReactInterval
            enabled
            timeout={2 * 60 * 1000}
            callback={() => this.getReleases()}
          />
        </div>
      </div>
    );
  }
}

class Release extends React.Component {
  static contextTypes = {
    authController: object.isRequired,
  };
  constructor(props) {
    super(props);
    this.state = {
      showModal: false,
      submitted: props.submitted,
      errorMsg: null,
    };
  }

  open = () => {
    this.setState({ showModal: true });
  };

  close = () => {
    this.setState({
      showModal: false,
      errorMsg: null,
    });
  };

  abortRelease = async (release) => {
    const url = `${config.API_URL}/releases/${release.name}`;
    if (!this.context.authController.userSession) {
      this.setState({ errorMsg: 'Login required!' });
      return;
    }
    const { accessToken } = this.context.authController.getUserSession();
    const headers = { Authorization: `Bearer ${accessToken}` };
    try {
      const response = await fetch(url, { method: 'DELETE', headers });
      if (!response.ok) {
        this.setState({ errorMsg: 'Auth failure!' });
        return;
      }
      this.setState({ submitted: true });
      window.location.reload();
    } catch (e) {
      this.setState({ errorMsg: 'Server issues!' });
      throw e;
    }
  };

  renderBody = () => {
    const { submitted, errorMsg } = this.state;
    if (errorMsg) {
      return (
        <div>
          <p>{errorMsg}</p>
        </div>
      );
    }
    if (!submitted) {
      return (
        <div>
          <h4>Are you sure?</h4>
          <p>
            The release will be cancelled!
          </p>
        </div>
      );
    }
    return (
      <div>Done.</div>
    );
  };

  render() {
    const { release } = this.props;
    return (
      <div className="row">
        <div className="col">
          <h3>
            <a href={`${config.TREEHERDER_URL}/#/jobs?repo=${release.project}&revision=${release.revision}`}>
              {release.product} <small>{release.version} build{release.build_number}</small>
            </a>
            <Button
              onClick={this.open}
              bsStyle="danger"
              bsSize="xsmall"
              style={{ margin: '10px' }}
              disabled={!this.context.authController.userSession}
            >
              Cancel release
            </Button>
          </h3>
        </div>
        <Modal show={this.state.showModal} onHide={this.close}>
          <Modal.Header closeButton>
            <Modal.Title>Cancel release</Modal.Title>
          </Modal.Header>
          <Modal.Body>
            {this.renderBody()}
          </Modal.Body>
          <Modal.Footer>
            <Button
              onClick={() => this.abortRelease(release)}
              bsStyle="danger"
              disabled={!this.context.authController.userSession}
            >
              Stop release
            </Button>
            <Button onClick={this.close} bsStyle="primary">Close</Button>
          </Modal.Footer>
        </Modal>
        <div className="col">
          <TaskProgress phases={release.phases} releaseName={release.name} />
        </div>
      </div>
    );
  }
}

const phaseStatus = async (phase, previousPhase) => {
  // Use TC status if task is submitted
  if (phase.submitted) {
    const status = await taskStatus(phase.actionTaskId);
    return status.status.state;
  }
  // FIrst phase, ready any time
  if (!previousPhase) {
    return 'ready';
  }
  // Phase is ready only when the previous one is submitted and the task is completed
  if (previousPhase.submitted) {
    // TODO: cache previous phase status
    const status = await taskStatus(previousPhase.actionTaskId);
    if (status.status.state === 'completed') {
      return 'ready';
    }
  }
  return 'blocked';
};

class TaskProgress extends React.Component {
  constructor(...args) {
    super(...args);
    this.state = {
      phasesWithStatus: [],
    };
  }

  async componentDidMount() {
    await this.syncPhases();
  }

  syncPhases = async () => {
    const { phases } = this.props;
    const phasesWithStatus = await Promise.all(phases.map(async (phase, idx, arr) => {
      const status = await phaseStatus(phase, arr[idx - 1]);
      return { ...phase, status };
    }));
    this.setState({ phasesWithStatus });
  };

  render() {
    const { phasesWithStatus } = this.state;
    const { releaseName } = this.props;
    const width = 100 / phasesWithStatus.length;
    return (
      <ProgressBar style={{ height: '40px', padding: '3px' }}>
        {phasesWithStatus.map(({
          name, submitted, actionTaskId, status,
        }) => (
          <ProgressBar
            key={name}
            bsStyle={statusStyles[status] || 'info'}
            now={width}
            active={submitted && status === 'running'}
            label={<TaskLabel
              key={actionTaskId}
              name={name}
              submitted={submitted}
              status={status}
              taskGroupUrl={`${config.TASKCLUSTER_TOOLS_URL}/groups/${actionTaskId}`}
              url={`${config.API_URL}/releases/${releaseName}/${name}`}
            />}
          />
        ))}
      </ProgressBar>
    );
  }
}

class TaskLabel extends React.PureComponent {
  static contextTypes = {
    authController: object.isRequired,
  };

  constructor(props) {
    super(props);
    this.state = {
      showModal: false,
      submitted: props.submitted,
      errorMsg: null,
    };
  }

  open = () => {
    this.setState({ showModal: true });
  };

  close = () => {
    this.setState({
      showModal: false,
      errorMsg: null,
    });
  };

  doEet = async () => {
    if (!this.context.authController.userSession) {
      this.setState({ errorMsg: 'Login required!' });
      return;
    }
    const { accessToken } = this.context.authController.getUserSession();
    const headers = { Authorization: `Bearer ${accessToken}` };
    try {
      const response = await fetch(this.props.url, { method: 'PUT', headers });
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
    const { submitted, errorMsg } = this.state;
    if (errorMsg) {
      return (
        <div>
          <p>{errorMsg}</p>
        </div>
      );
    }
    if (!submitted) {
      return (
        <div>
          <h4>Are you sure?</h4>
          <p>Action will be scheduled</p>
        </div>
      );
    }
    return (
      <div>
        Action task has been submitted.
      </div>
    );
  };

  render() {
    const { status, name, taskGroupUrl } = this.props;
    if (status === 'blocked') {
      return (
        <div>
          <Button disabled bsStyle={statusStyles[status]}>{name}</Button>
        </div>
      );
    }
    if (status === 'ready') {
      return (
        <div>
          <Button bsStyle="primary" onClick={this.open}>{name}</Button>
          <Modal show={this.state.showModal} onHide={this.close}>
            <Modal.Header closeButton>
              <Modal.Title>Do eet</Modal.Title>
            </Modal.Header>
            <Modal.Body>
              {this.renderBody()}
            </Modal.Body>
            <Modal.Footer>
              <Collapse in={!this.state.submitted}>
                <div>
                  <Button
                    onClick={this.doEet}
                    bsStyle="danger"
                    disabled={!this.context.authController.userSession && !this.state.submitted}
                  >
                    Do eet!
                  </Button>
                  <Button onClick={this.close} bsStyle="primary">Close</Button>
                </div>
              </Collapse>
            </Modal.Footer>
          </Modal>
        </div>
      );
    }
    return (
      <div>
        <Button bsStyle={statusStyles[status]} href={taskGroupUrl}>{name}</Button>
      </div>
    );
  }
}
