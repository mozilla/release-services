import React from 'react';
import app from './index';
import url from 'url';
import { Map } from 'immutable';
import { delay } from 'redux-saga';
import { push } from 'react-router-redux'
import { take, fork, call, race, put } from 'redux-saga/effects'
import { watchFor, watchForRoute, parseCredentials } from './common';



/* -- action types -- */

export const SIGN_IN = 'LOGIN.SIGN_IN';
export const SIGN_IN_SUCCESS = 'LOGIN.SIGN_IN_SUCCESS';
export const SIGN_IN_ERROR= 'LOGIN.SIGN_IN_ERROR';
export const SIGN_OUT = 'LOGIN.SIGN_OUT';


/* -- sagas io functions -- */

const CREDENTIALS_KEY = 'relengapi_login';

const getCredentials = () => (
  JSON.parse(window.localStorage.getItem(CREDENTIALS_KEY))
);

const setCredentials = credentials => {
  window.localStorage.setItem(CREDENTIALS_KEY, JSON.stringify(credentials));
};

const removeCredentials = () => {
  window.localStorage.removeItem(CREDENTIALS_KEY);
};

const redirectTo = url => {
  window.location = url;
};

const buildLoginURL = () => (
  url.format({
    protocol: 'https',
    host: 'login.taskcluster.net',
    query: {
      target: url.format({
        protocol: window.location.protocol,
        host: window.location.host,
        pathname: '/login'
      }),
      description: "RelengAPI services."
    }
  })
);


/* -- sagas -- */

const authentication = initialQuery => function*() {
  while (true) {
    let expires_in = 1000 * 60 * 5;  // expires in 5min
    let credentials = yield call(getCredentials);

    if (credentials) {
      yield put({ type: SIGN_IN_SUCCESS, payload: credentials });

    } else {
      yield take(SIGN_IN)

      // login requested redirect to login page if no url query provided
      if (initialQuery === "") {
        yield call(redirectTo, buildLoginURL());
        return;
      }

      credentials = parseCredentials(initialQuery);

      if (credentials) {
        yield call(setCredentials, credentials);
        yield put({ type: SIGN_IN_SUCCESS, payload: credentials });
        yield call(app.history.push, { pathname: '/' });
      } else {
        yield call(removeCredentials);
        yield put({ type: SIGN_IN_ERROR });
      }

    }

    if (credentials.certificate && credentials.certificate.expiry) {
      expires_in = 1000 * (new Date(credentials.certificate.expiry) - new Date())
    }

    const {signOut, expired} = yield race({
      signOut: take(SIGN_OUT),
      expired: call(delay, expires_in)
    });

    if (signOut || expired) {
        console.log("signout");
      yield call(removeCredentials);
    }
  }
};

export const sagas = [
  fork(authentication(window.location.search)),
  fork(watchForRoute(window.location.pathname, '/login', { type: SIGN_IN }))
];

export const reducers = (state = Map(), action) => {
    switch (action.type) {
      case SIGN_IN_SUCCESS:
        return state.set('credentials', action.payload);
      case SIGN_OUT:
        console.log("signout2");
        return state.delete('credentials');
      default:
        return state;
    };
};

export const Login = () => {
  return <h1>Login</h1>
}
Login.__name__ = 'Login'

export default Login;
