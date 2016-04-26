import React from 'react';  // needed for jsx to work

/* --- DevTools ------------------------------------------------------------ */

import { compose } from 'redux';
import { createDevTools, persistState } from 'redux-devtools';

import ChartMonitor from 'redux-devtools-chart-monitor';
import DockMonitor from 'redux-devtools-dock-monitor';
import LogMonitor from 'redux-devtools-log-monitor';
import SliderMonitor from 'redux-slider-monitor';

let DEVTOOLS_STORE;
let DEVTOOLS = '';

/* istanbul ignore next */
if (__DEV__) {
  DEVTOOLS = createDevTools(
    <DockMonitor toggleVisibilityKey="ctrl-h"
                changePositionKey="ctrl-q"
                changeMonitorKey="ctrl-m"
                defaultVisible="true"
                >
      <LogMonitor />
      <SliderMonitor />
      <ChartMonitor />
    </DockMonitor>
  );
  DEVTOOLS_STORE = compose(
    window.devToolsExtension ? window.devToolsExtension() : DEVTOOLS.instrument(),
    persistState(window.location.href.match(/[?&]debug_session=([^&]+)\b/))
  );
}

/* --- Routes -------------------------------------------------------------- */

import BadPenny from './badpenny';
import Clobberer from './clobberer';
import Home from './home';
import SlaveLoad from './slaveload';
import Tokens from './tokens';
import ToolTool from './tooltool';
import TreeStatus from './treestatus';


export const routes = [
  {
    path: '/',
    title: 'Home',
    component: Home
  },
  {
    path: '/badpenny',
    title: 'Bad Penny',
    component: BadPenny
  },
  {
    path: '/clobberer',
    title: 'Clobberer',
    component: Clobberer
  },
  {
    path: '/slaveload',
    title: 'Slave Load',
    component: SlaveLoad
  },
  {
    path: '/tokens',
    title: 'Tokens',
    component: Tokens
  },
  {
    path: '/tooltool',
    title: 'ToolTool',
    component: ToolTool
  },
  {
    path: '/treestatus',
    title: 'Tree Status',
    component: TreeStatus
  }
];


/* --- Store --------------------------------------------------------------- */

import Immutable from 'immutable';
import { LOCATION_CHANGE, syncHistoryWithStore } from 'react-router-redux'
import { browserHistory } from 'react-router';
import { combineReducers } from 'redux-immutable';
import { createStore } from 'redux';


export const initialState = Immutable.fromJS({});

export const routerReducer = (state = initialState, action) => {
  if (action.type === LOCATION_CHANGE) {
    return state.merge({
      locationBeforeTransitions: action.payload
    });
  }
  return state;
};

export const reducers = {};

export const store = createStore(
  combineReducers({ ...reducers, routing: routerReducer }),
  initialState,
  DEVTOOLS_STORE
);

export const history = syncHistoryWithStore(browserHistory, store, {
  selectLocationState: state => state.get('routing').toJS()
});

/* --- Layout -------------------------------------------------------------- */

import { Link } from 'react-router';

export const Layout = ({ children }) => (
  <div className="container">
    <nav id="navbar" className="navbar navbar-light bg-faded">
      <button className="navbar-toggler hidden-sm-up" type="button"
              data-toggle="collapse" data-target="#navbar-header"
              aria-controls="navbar-header">&#9776;</button>
      <div className="collapse navbar-toggleable-xs" id="navbar-header">
        <ul className="nav navbar-nav">
        {
          routes.map((route) => (
            <li key={route.path} className="nav-item active">
              <Link className="nav-link" to={route.path}>{route.title}</Link>
            </li>
          ))
        }
        </ul>
      </div>
    </nav>
    <main id="content">{children}</main>
    <DEVTOOLS />
  </div>
)
Layout.__name__ = 'Layout'
Layout.propTypes = {
  children: React.PropTypes.node
}
