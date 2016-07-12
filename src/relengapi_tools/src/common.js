import React from 'react';
import fetch from 'isomorphic-fetch';
import querystring from 'querystring';
import { put, take } from 'redux-saga/effects'
import { takeLatest } from 'redux-saga'
import { LOCATION_CHANGE } from 'react-router-redux';


export const Loading = (props)  => {
  if (props.loading === true) {
    return (
      <div className="progress-wrapper">
        <progress className="progress progress-striped progress-animated"
                  value="100" max="100">Loading ...</progress>
        <span>Loading ...</span>
      </div>
    );
  } else if (props.error) {
    return (
      <div className="alert alert-danger" role="alert">
        <strong>Error: </strong>
        <span>{props.error}.</span>
        <a className="alert-link" href="#" onClick={props.onRetry}> Click to retry.</a>
      </div>
    );
  } else {
    return <props.component {...props} />;
  }
};

export const Dropdown = (props) => {
  let {
    selected = null,
    options = [],
    placeholder = '',
    onSelect
  } = props;
  return (
    <div className="btn-group btn-dropdown">
      <span type="button" className="btn btn-secondary dropdown-toggle"
            data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
        {(options.reduce((r, o) => o.id === selected ? o.title : r, null)) || placeholder}
      </span>
      <span type="button" className="btn btn-secondary dropdown-toggle"
            data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
        <span className="sr-only">Toggle Dropdown</span>
      </span>
      <div className="dropdown-menu">
      {
        options.map(option => (
          <a className="dropdown-item" key={option.id} onClick={onSelect(option.id)}>
            {option.title}
          </a>
        ))
      }
      </div>
    </div>
  );
};

export const fetchJSON = (url, options) => {
  return fetch(url, options)
    .then(response => {
      if (response.status >= 200 && response.status < 300) {
        return response.json()
      }
      const error = new Error(response.statusText);
      error.response = response;
      return error;
    })
    .catch(e => {
      const error = new Error(e.message);
      error.response = e;
      return error
    });
};

export const watchFor = (pattern, saga) => function*() {
  yield takeLatest(pattern, saga);
};

export const watchForRoute = (initialPathname, pathname, action) => {
  return function*() {
    if (initialPathname === pathname) {
        yield put(action);
    }
    let location_action = null;
    while (location_action = yield take(LOCATION_CHANGE)) {
      if (location_action.payload.pathname === pathname) {
        yield put(action);
      }
    }
  };
};

export const parseCredentials = query => {
  try {
    let credentials = querystring.parse(query.substr(1)) ;
    if (!credentials.clientId || !credentials.accessToken) {
      return null;
    }
    if (credentials.certificate && typeof(credentials.certificate) === "string") {
      credentials.certificate = JSON.parse(credentials.certificate);
    }
    return credentials;
  } catch (e) {
    return null;
  }
}
