/* TODO: explain what this file is about
 *
 */
import React from 'react';
import { union } from 'tagmeme';
import {
  Alert,
  ListGroup,
  ListGroupItem,
  ListGroupItemHeading,
  ListGroupItemText,
} from 'reactstrap';

import withLayout from './../layout';
import RemoteData from './../remotedata';
import { notAskedView, loadingView, failureView } from './../views/remotedata';


const Msg = union([
  'FETCH_RELEASES',
]);


const init = ({ listReleases }) => [
  {
    releases: listReleases.initModel,
  },
  // immediately start fetching releases
  listReleases.initEffect,
];

const update = ({ listReleases }) => (msg, model) => {
  console.log('== UPDATE ==');
  const [newModel, newEffect] = listReleases.update(msg, model);
  return [newModel, newEffect];
};

const viewRelease = release => (
  <ListGroupItem>
    <ListGroupItemHeading>{release.product} <small>{release.version}</small></ListGroupItemHeading>
    <ListGroupItemText>TODO</ListGroupItemText>
  </ListGroupItem>
);

const viewReleases = (releases, dispatch) => (
  (releases.data.length === 0)
    ? <Alert color="info">No releases can be found.</Alert>
    : <ListGroup>{releases.data.map(release => viewRelease(release, dispatch))}</ListGroup>
);

const view = ({ listReleases }) => (model, dispatch) => (
  <React.Fragment>
    <h2>Releases in progress</h2>
    {listReleases.view(model, dispatch, notAskedView(), loadingView, failureView, viewReleases)}
  </React.Fragment>
);

let program = null;
export const createProgram = (options, effects) => {
  if (program === null) {
    const listReleases = RemoteData('releases', Msg.FETCH_RELEASES, effects.listReleases());
    program = {
      init: init({ listReleases }),
      update: update({ listReleases }),
      view: view({ listReleases }),
    };
    console.log(program);
  }
  return program;
};

export default withLayout(createProgram);
