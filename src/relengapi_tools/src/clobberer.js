import React from 'react';
import { LOCATION_CHANGE } from 'react-router-redux';
import { Map } from 'immutable';
import { call, fork, put, take, race } from 'redux-saga/effects'
import { combineReducers } from 'redux-immutable';
import { connect } from 'react-redux';
import { takeLatest, delay } from 'redux-saga';

import { Loading, Dropdown, fetchJSON } from './common';
import { routes } from './layout';
import { app } from './';

// --- helpers ---

const url = (path) => (process.env.NEO_CLOBBERER_BASE_URL || '/__api__/clobberer') + path;
const TIMEOUT = parseInt(process.env.NEO_CLOBBERER_FETCH_TIMEOUT || '60', 10);


// --- actions ---


const fetchBranches = type => {
  return {
    type: 'CLOBBERER.' + type.toUpperCase() + '.FETCH'
  };
};

const clobber = (type, items) => {
  return {
    type: 'CLOBBERER.' + type.toUpperCase() + '.CLOBBER',
    payload: items
  };
};

const selectBranch = (type, selected) => {
  return {
    type: 'CLOBBERER.' + type.toUpperCase() + '.SELECT',
    payload: selected
  };
};

const selectBranchItem = (type, branch, items) => {
  return {
    type: 'CLOBBERER.' + type.toUpperCase() + '.TABLE_SELECT',
    payload: { branch, items } 
  };
};

const deselectBranchItem = (type, branch, items) => {
  return {
    type: 'CLOBBERER.' + type.toUpperCase() + '.TABLE_DESELECT',
    payload: { branch, items }
  };
};



// --- Sagas ---

const fetchBranchesForReal = type => {
  return function*() {
    const { response, timeout } = yield race({
        response: call(fetchJSON, url('/' + type)),
        timeout: call(delay, TIMEOUT * 1000)
    });

    if (response) {
      if (response instanceof Error) {
        yield put({
          type: 'CLOBBERER.' + type.toUpperCase() + '.FETCH_FAILED',
          payload: response
        });
      } else {
        yield put({
          type: 'CLOBBERER.' + type.toUpperCase() + '.FETCH_SUCCESS',
          payload: response
        });
      }
    } else {
      yield put({
        type: 'CLOBBERER.' + type.toUpperCase() + '.FETCH_FAILED',
        payload: 'Timeout (' + TIMEOUT + ') reached!'
      });
    }
  }
};

const watchFetchBranches = type => {
  return function* () {
    yield takeLatest(
      'CLOBBERER.' + type.toUpperCase() + '.FETCH',
      fetchBranchesForReal(type)
    );
  };
};


const watchToClobber = type => {
  return function*() {
    let action = null;
    while (action = yield take('CLOBBERER.' + type.toUpperCase() + '.CLOBBER')) {
      const { response, timeout } = yield race({
        response: call(fetchJSON, url('/' + type), {
            method: 'POST',
            headers: {
              'Accept': 'application/json',
              'Content-Type': 'application/json'
            },
            body: JSON.stringify(action.payload)
        }),
        timeout: call(delay, TIMEOUT * 1000)
      });

      if (response) {
        if (response instanceof Error) {
          yield put({
            type: 'CLOBBERER.' + type.toUpperCase() + '.CLOBBER_FAILED',
            payload: response
          });
        } else {
          yield put({
            type: 'CLOBBERER.' + type.toUpperCase() + '.CLOBBER_SUCCESS',
            payload: response
          });
        }
      } else {
        yield put({
          type: 'CLOBBERER.' + type.toUpperCase() + '.CLOBBER_FAILED',
          payload: 'Timeout reached!'
        });
      }
    }
  };
};

const initialFetch = (type, initialPathname) => {
  return function*() {
    if (initialPathname === Clobberer.__path__) {
        yield put(fetchBranches(type));
    }
    let action = null;
    while (action = yield take(LOCATION_CHANGE)) {
      if (action.payload.pathname === Clobberer.__path__) {
        yield put(fetchBranches(type));
      }
    }
  };
};

export const sagas = [
   fork(watchToClobber('taskcluster')),
   fork(watchToClobber('buildbot')),
   fork(watchFetchBranches('taskcluster')),
   fork(watchFetchBranches('buildbot')),
   fork(initialFetch('taskcluster', window.location.pathname)),
   fork(initialFetch('buildbot', window.location.pathname))
];

// --- END: sagas ---



const reducerFor = type => (state = Map(), action) => {
    switch (action.type) {

      case 'CLOBBERER.' + type.toUpperCase() + '.CLOBBER':
        return state.set('clobbering', true);

      case 'CLOBBERER.' + type.toUpperCase() + '.CLOBBER_FAILED':
        return state.set('clobbering', false);

      case 'CLOBBERER.' + type.toUpperCase() + '.CLOBBER_SUCCESS':
        return state.set('clobbering', false);

      case 'CLOBBERER.' + type.toUpperCase() + '.FETCH':
        return state.set('loading', true)
                    .set('error', null)
                    .set('options', [])
                    .set('selected', null)
                    .set('table_selected', {})
                    .set('data', {});

      case 'CLOBBERER.' + type.toUpperCase() + '.FETCH_FAILED':
        return state.set('loading', false)
                    .set('error', action.payload);

      case 'CLOBBERER.' + type.toUpperCase() + '.FETCH_SUCCESS':

        if (action.payload.error) {
            return state.set('loading', false)
                        .set('error', 'Something went wrong');
        }

        let options = action.payload.result.map(x => {
          return { id: x.name, title: x.name };
        });
        let data = action.payload.result.reduce((r, x) => {
          r[x.name] = x.data;
          return r;
        }, {});

        return state.set('loading', false)
                    .set('options', options)
                    .set('data', data);

      case 'CLOBBERER.' + type.toUpperCase() + '.SELECT':
        return state.set('selected', action.payload);

      case 'CLOBBERER.' + type.toUpperCase() + '.TABLE_SELECT':
        var { branch, items } = action.payload;

        var table_selected = state.get('table_selected') || {};
        table_selected[branch] = table_selected[branch] || [];

        table_selected[branch] = table_selected[branch].concat(
            items.filter(x => table_selected[branch].indexOf(x) === -1))

        return state.set('table_selected', table_selected);

      case 'CLOBBERER.' + type.toUpperCase() + '.TABLE_DESELECT':
        var { branch, items } = action.payload;

        var table_selected = state.get('table_selected') || {};
        table_selected[branch] = table_selected[branch] || [];

        table_selected[branch] = table_selected[branch].filter(x => items.indexOf(x) === -1)

        return state.set('table_selected', table_selected);

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
      clobber: items => () => {
        dispatch(clobber(type, items));
      },
      onRetry: selected => () => {
        dispatch(fetchBranches(type));
      },
      onSelect: selected => () => {
        dispatch(selectBranch(type, selected));
      },
      onTableSelect: (branch, items) => () => {
        dispatch(selectBranchItem(type, branch, items));
      },
      onTableDeselect: (branch, items) => () => {
        dispatch(deselectBranchItem(type, branch, items));
      }
    }
  }
];
    

const BranchesContent = type => props => {
  return <div>
    {
      props.clobbering === true
        ? (
          <button className="btn btn-primary btn-large"
                  disabled="disabled">
            Clobbering ({
              props.table_selected
                ? Object.keys(props.table_selected).reduce(
                    (r, x) => r + props.table_selected[x].length, 0)
                : 0
            }) ...
          </button>
          )
        : (
          <button className="btn btn-primary btn-large"
                  onClick={props.clobber(props.table_selected)}
                  disabled={!props.table_selected || props.table_selected.length === 0 ? "disabled" : ""}>
            Submit clobberer ({
              props.table_selected
                ? Object.keys(props.table_selected).reduce(
                    (r, x) => r + props.table_selected[x].length, 0)
                : 0
            })
          </button>
          )
    }
    {
      !props.table_selected || Object.keys(props.table_selected).length === 0
        ? <div className="clobberer-submit-description"></div>
        : (
          <div className="clobberer-submit-description">
            <a data-toggle="collapse" href={"#clobberer-" + type + "-selected"}
               aria-expanded="false" aria-controls="collapseExample">
              Show/Hide selected&nbsp;
              { type === 'buildbot' ? ' builder(s)' : ' worker type(s)' }&nbsp;
              to be clobbered
            </a>
            <ul id={"clobberer-" + type + "-selected"} className={props.show_selected ? "collapse in" : "collapse"} >
            {
              Object.keys(props.table_selected).map(branch => (
                props.table_selected[branch].map(item => (
                  <li key={branch + "_" + item}>
                    <div><b>Branch:</b> {branch}</div>
                    <div><b>{ type === 'buildbot' ? ' Builder' : 'i Worker Type' }:</b> {item}</div>
                  </li>
                ))
              ))
            }
            </ul>
          </div>
        )
    }
    <Dropdown {...props} />
    {
      props.selected ? (
        <table className="table table-hover">
          <thead>
            <tr>
              <th>
                 <input type="checkbox"
                    onChange={
                      Object.keys(props.data[props.selected]).every(x => (props.table_selected[props.selected] || []).indexOf(x) !== -1)
                        ? props.onTableDeselect(props.selected, Object.keys(props.data[props.selected]))
                        : props.onTableSelect(props.selected, Object.keys(props.data[props.selected]))
                    }
                    checked={
                      Object.keys(props.data[props.selected]).every(x => (props.table_selected[props.selected] || []).indexOf(x) !== -1)
                        ? "checked"
                        : ""
                    }
                    />
              </th>
              <th>{type === 'buildbot' ? 'Builder' : 'Worker Type'}</th>
              <th>{type === 'buildbot' ? 'Last clobber' : 'Caches'}</th>
            </tr>
          </thead>
          <tbody>
          {
            Object.keys(props.data[props.selected]).map(x => (
              <tr key={x}>
                <td>
                  <input type="checkbox"
                         onChange={
                           (props.table_selected[props.selected] || []).indexOf(x) !== -1
                             ? props.onTableDeselect(props.selected, [x])
                             : props.onTableSelect(props.selected, [x])
                         }
                         checked={
                           (props.table_selected[props.selected] || []).indexOf(x) !== -1
                             ? "checked"
                             : ""
                         }
                         />
                </td>
                <td>{x}</td>
                <td>
                  <ul>{ props.data[props.selected][x].map(y => <li key={y}>{y}</li>) }</ul>
                </td>
              </tr>
            ))
          }
          </tbody>
        </table>
      ) : ()=>null
    }
  </div>
};

const Branches = type => React.createElement(connect(...mapToProps(type))(props => (
  <Loading {...props} placeholder="Select branch ..." component={BranchesContent(type)} />
)));

export const Clobberer = () => (
  <div>
    <div id="banner-not-home"></div>
    <div className="container">
      <h1>{ Clobberer.__name__ }</h1>
      <p>{ routes.getIn(['clobberer', 'description']) }</p>
      <p>TODO: link to documentation</p>
      <div className="row">
        <div className="col-md-6">
          <h2>Taskcluster</h2>
          {Branches('taskcluster')}
        </div>
        <div className="col-md-6">
          <h2>Buildbot</h2>
          {Branches('buildbot')}
        </div>
      </div>
    </div>
  </div>
)

Clobberer.__name__ = 'Clobberer'
Clobberer.__path__ = '/clobberer'

export default Clobberer;
