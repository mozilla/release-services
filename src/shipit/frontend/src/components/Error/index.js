import React from 'react';
import { Alert, Button, Collapse } from 'react-bootstrap';

export default class Error extends React.PureComponent {
  constructor(props) {
    super(props);
    this.state = {};
  }

  getTitle() {
    const { error } = this.props;

    if (error.body && error.body.code) {
      return `Error ${error.body.code} `;
    }

    if (error.response && error.response.status) {
      return `HTTP ${error.response.status} `;
    }

    return 'Error ';
  }

  handleOpen = () => this.setState({ open: !this.state.open });

  render() {
    const { error } = this.props;
    const { open } = this.state;

    return (
      <Alert bsStyle="danger">
        <strong>{this.getTitle()}</strong>
        <pre>{error.message}</pre>
        {process.env.NODE_ENV === 'development' && (
          <div>
            Stack (development only):<pre>{error.stack}</pre>
          </div>
        )}
        {error.body &&
          error.body.requestInfo && (
            <div>
              <Button bsSize="xsmall" onClick={this.handleOpen}>
                Additional details...
              </Button>
              <Collapse in={open}>
                <pre>{JSON.stringify(error.body.requestInfo, null, 2)}</pre>
              </Collapse>
            </div>
          )}
      </Alert>
    );
  }
}
