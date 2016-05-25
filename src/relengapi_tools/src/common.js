import React from 'react';

export const Loading = (props, children)  => {
  if (props.loading === false)
      return <children {...props} />;
  else
      return (
        <div className="progress-wrapper">
          <progress className="progress progress-striped progress-animated"
                    value="100" max="100">Loading ...</progress>
          <span>Loading ...</span>
        </div>
      );
};

export const Dropdown = ({ selected=null, options=[], placeholder='', onChange }) => {
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
