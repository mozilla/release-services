import React from 'react';
import fetch from 'isomorphic-fetch';

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
        <a className="alert-link" href="#" onClick={props.reload}> Click to retry.</a>
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
    onChange
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
          <a className="dropdown-item" key={option.id} onClick={onChange(option.id)}>
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
    .then(response => response.json())
    .then(response => response);
};
