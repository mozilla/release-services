require('expose?$!expose?jQuery!jquery')
require('expose?Tether!tether')
require('bootstrap')
require("!style!css!sass!./index.scss")

import React from 'react'
import ReactDOM from 'react-dom'
import { Provider } from 'react-redux'
import { Router, Route } from 'react-router'

import { store, history, Layout, routes } from './app'


ReactDOM.render((
    <Provider store={store}>
        <Router history={history}>
            <Route component={Layout}>
            {
              routes.map(function(route) {
                return <Route key={route.path} path={route.path} component={route.component} />;
              })
            }
            </Route>
        </Router>
    </Provider>
), document.getElementById('app'))
