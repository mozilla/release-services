import React from 'react';
import { connect } from 'react-redux';
import { combineReducers } from 'redux-immutable';
import { Map } from 'immutable';
import { routes } from './layout';
import { Loading, Dropdown } from './common';

// TODO: in future we could make this one big tree
// eg. http://jsfiddle.net/infiniteluke/908earbh/9/

// --- actions ---

const initialFetch = type => {
  return {
    type: 'CLOBBERER.' + type.toUpperCase() + '.FETCH_BRANCHES'
  };
};

const selectBranch = (type, selected) => {
  return {
    type: 'CLOBBERER.' + type.toUpperCase() + '.SELECT_ITEM',
    payload: selected
  };
};

// --- END: actions ---


const reducerFor = type => (state = Map(), action) => {
    switch (action.type) {
      case 'CLOBBERER.' + type.toUpperCase() + '.SELECT_ITEM':
        return state.set('selected', action.payload);
      default:
        return state;
    };
};

export const reducers = combineReducers({
    taskcluster: reducerFor('taskcluster'),
    buildbot: reducerFor('buildbot')
});


const mapToProps = type => [
  state => state.getIn(['clobberer', type], Map()).toJS(),
  (dispatch, props) => {
    return {
      onChange: (selected) => () => {
        dispatch(selectBranch(type, selected));
      }
    }
  }
];
    
const Taskcluster = connect(...mapToProps('taskcluster'))(props => {
  return <Dropdown {...props} placeholder="Select branch ..." />
});

const Buildbot = connect(...mapToProps('buildbot'))(props => {
  return <Dropdown {...props} placeholder="Select branch ..." />
});


export const Clobberer = () => (
  <div>
    <div id="banner-not-home"></div>
    <div className="container">
      <h1>Clobberer</h1>
      <p>{ routes.getIn(['clobberer', 'description']) }</p>
      <p>TODO: link to documentation</p>
      <div className="row">
        <div className="col-sm-6">
          <h2>Taskcluster</h2>
          <Taskcluster/>
        </div>
        <div className="col-sm-6">
          <h2>Buildbot</h2>
          <Buildbot/>
        </div>
      </div>
    </div>
  </div>
)

Clobberer.__name__ = 'Clobberer'

export default Clobberer;
