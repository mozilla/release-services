import React from 'react';
import { Map } from 'immutable';
import { call, fork, put } from 'redux-saga/effects'
import { combineReducers } from 'redux-immutable';
import { connect } from 'react-redux';
import { takeLatest } from 'redux-saga';

import { Loading, Dropdown, fetchJSON } from './common';
import { routes } from './layout';
import { app } from './';

// --- helpers ---

const url = (path) => (process.env.NEO_CLOBBERER_BASE_URL || '/__api__/clobberer') + path;


// --- actions ---

const fetchBranches = type => {
  return {
    type: 'CLOBBERER.' + type.toUpperCase() + '_BRANCHES.FETCH'
  };
};

const selectBranch = (type, selected) => {
  return {
    type: 'CLOBBERER.' + type.toUpperCase() + '_BRANCHES.SELECT',
    payload: selected
  };
};


// --- Sagas ---

const fetchBranchesForReal = type => {
  return function*() {
    try {
      const response = yield call(fetchJSON, url('/' + type + '/branches'));
      yield put({
        type: 'CLOBBERER.' + type.toUpperCase() + '_BRANCHES.FETCH_SUCCESS',
        payload: response
      });
    } catch (e) {
      yield put({
        type: 'CLOBBERER.' + type.toUpperCase() + '_BRANCHES.FETCH_FAILED',
        payload: e.message
      });
    }
  }
};

const watchFetchBranches = type => {
  return function* () {
    yield takeLatest(
      'CLOBBERER.' + type.toUpperCase() + '_BRANCHES.FETCH',
      fetchBranchesForReal(type)
    );
  };
};

const initialFetch = type => {
  return function*() {
    yield put(fetchBranches(type));
  };
};

export const sagas = [
   fork(watchFetchBranches('taskcluster')),
   fork(watchFetchBranches('buildbot')),
   fork(initialFetch('taskcluster')),
   fork(initialFetch('buildbot'))
];

// --- END: sagas ---



const reducerFor = type => (state = Map(), action) => {
    switch (action.type) {
      case 'CLOBBERER.' + type.toUpperCase() + '_BRANCHES.FETCH':
        return state.set('loading', true);
      case 'CLOBBERER.' + type.toUpperCase() + '_BRANCHES.FETCH_FAILED':
        return state.set('loading', false)
                    .set('error', action.payload);
      case 'CLOBBERER.' + type.toUpperCase() + '_BRANCHES.FETCH_SUCCESS':

        if (action.payload.error) {
            return state.set('loading', false)
                        .set('error', 'Something went wrong');
        }
        return state.set('loading', false)
                    .set('options', action.payload.result.map(x => {
                        return { id: x.name, title: x.name };
                    }));
      case 'CLOBBERER.' + type.toUpperCase() + '_BRANCHES.SELECT':
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
  state => {

    return state.getIn(['clobberer', type], Map()).toJS()
  },
  (dispatch, props) => {
    return {
      reload: selected => () => {
        dispatch(fetchBranches(type));
      },
      onChange: selected => () => {
        dispatch(selectBranch(type, selected));
      }
    }
  }
];
    
const BranchesDropdown = type => connect(...mapToProps(type))(props => {
  return (
    <Loading {...props} placeholder="Select branch ..." component={Dropdown} />
  );
});
const TaskclusterBranches = BranchesDropdown('taskcluster');
const BuildbotBranches = BranchesDropdown('buildbot');

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
          <TaskclusterBranches/>
        </div>
        <div className="col-sm-6">
          <h2>Buildbot</h2>
          <BuildbotBranches/>
        </div>
      </div>
    </div>
  </div>
)

Clobberer.__name__ = 'Clobberer'

export default Clobberer;
