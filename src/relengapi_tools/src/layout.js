import React from 'react';
import {connect} from 'react-redux';
import {Link} from 'react-router';
import {fromJS} from 'immutable';
import classNames from  'classnames';

const NOOP = () => null;

export const routes = fromJS({
  home: { path: '/', title: 'RelengAPI',
          banner: 'Collection of Release Engineering services.' },
  login: { path: '/login', title: 'Login' },
  badpenny: { path: '/badpenny' , title: 'BadPenny' },
  clobberer: { path: '/clobberer' , title: 'Clobberer',
               description: 'A repairer of buildbot builders and taskcluster worker types.' },
  slaveloan: { path: '/slaveloan', title: 'SlaveLoan' },
  tokens: { path: '/tokens', title: 'Tokens' },
  tooltool: { path: '/tooltool', title: 'ToolTool' },
  treestatus: { path: '/treestatus', title: 'TreeStatus' }
});

export const services = [
  routes.get('badpenny'),
  routes.get('clobberer'),
  routes.get('slaveloan'),
  routes.get('tokens'),
  routes.get('tooltool'),
  routes.get('treestatus')
];

const mapToProps = [
  state => {
    const path = state.getIn(['routing', 'locationBeforeTransitions', 'pathname']);
    return {
      login: state.get('login'),
      current_route: routes.keySeq().reduce((result, routeName) => {
        return routes.getIn([routeName, 'path']) === path ? routes.get(routeName).toJS() : result
      }, {})
    };
  },
  (dispatch, props) => {
    return {
      logout: () => {
        dispatch({ type: 'LOGIN.SIGN_OUT' });
      },
    };
  }
];


export const Layout = ({ login, logout, children=NOOP, current_route={} }) => (
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
            <li key="services" className="nav-item">
              <div className="dropdown">
                <a className="nav-link dropdown-toggle" id="dropdownServices" data-toggle="dropdown"
                   aria-haspopup="true" aria-expanded="false">
                  Services
                </a>
                <div className="dropdown-menu dropdown-menu-right" aria-labelledby="dropdownServices">
                {
                  services.map(route=> (
                      <Link key={route.get('path')} className="dropdown-item" to={route.get('path')}>
                        {route.get('title')}
                      </Link>
                    ))
                }
                </div>
              </div>
            </li>
            <li key="login" className="nav-item">
              { 
                login.has('credentials')
                 ? (
                  <a className="nav-link" href="#" onClick={logout}>
                    Logout
                  </a>
                 ) : (
                  <Link className="nav-link" to={routes.getIn(['login', 'path'])}>
                    {routes.getIn(['login', 'title'])}
                  </Link>
                 )
              }
            </li>
          </ul>
        </div>
      </div>
    </nav>
    {
      current_route.banner === undefined ? (
        <div id="banner-empty"></div>
      ) : (
        <div id="banner">
          <div className="container">
            {current_route.banner}
          </div>
        </div>
      )
    }
    <div id="content">
      <div className="container">
        {children}
      </div>
    </div>
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

export default connect(...mapToProps)(Layout)
