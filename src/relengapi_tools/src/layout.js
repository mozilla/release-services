import React from 'react';
import {connect} from 'react-redux';
import {Link} from 'react-router';
import {fromJS} from 'immutable';
import classNames from  'classnames';

const NOOP = () => null;

export const routes = fromJS({
  home: { path: '/', title: 'RelengAPI' },
  badpenny: { path: '/badpenny' , title: 'BadPenny' },
  clobberer: { path: '/clobberer' , title: 'Clobberer',
               description: 'A repairer of buildbot builders and taskcluster worker types.' },
  slaveloan: { path: '/slaveloan', title: 'SlaveLoan' },
  tokens: { path: '/tokens', title: 'Tokens' },
  tooltool: { path: '/tooltool', title: 'ToolTool' },
  treestatus: { path: '/treestatus', title: 'TreeStatus' }
});


export const mapStateToProps = state => {
  const path = state.getIn(['routing', 'locationBeforeTransitions', 'pathname']);
  return {
    current_route: routes.keySeq().reduce((result, routeName) => {
      routes.getIn([routeName, 'path']) === path ? routes.get(routeName).toJS() : result
    }, {})
  };
};


export const Layout = ({ children=NOOP, current_route={} }) => (
  <div>
    <nav id="navbar" className="navbar navbar-full navbar-light">
      <div className="container">
        <button className="navbar-toggler hidden-md-up" type="button"
                data-toggle="collapse" data-target=".navbar-collapse"
                aria-controls="navbar-header">&#9776;</button>

        <Link className="navbar-brand"
              to={routes.getIn(['home', 'path'])}>
          {routes.getIn(['home', 'title'])}
        </Link>
        <div className="collapse navbar-toggleable-sm navbar-collapse pull-right">
          <ul className="nav navbar-nav">
          {
            routes.keySeq()
              .filter(x => x !== 'home')
              .map(x=> (
                <li key={x}
                    className={
                      classNames({
                        'nav-item': true,
                        'active': current_route.path === routes.getIn([x, 'path'])
                      })}>
                <Link className="nav-link" to={routes.getIn([x, 'path'])}>
                  {routes.getIn([x, 'title'])}
                </Link>
              </li>
            ))
          }
          </ul>
        </div>
      </div>
    </nav>
    <div id="content">{children}</div>
    <footer className="container">
      <hr/>
      <ul>
        <li><a key="github" href="#">Github</a></li>
        <li><a key="contribute" href="#">Contribute</a></li>
        <li><a key="contact" href="#">Contact</a></li>
      </ul>
    </footer>
  </div>
);

export default connect(mapStateToProps)(Layout)
