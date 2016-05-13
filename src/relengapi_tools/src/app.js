import React from 'react'
import {Link} from 'react-router'
import {createApp} from 'neo'

import Home from './home'

export const Routes = [
  { path: '/', title: 'Home', component: Home }
];

export const Layout = ({ children }) => (
  <div className="container">
    <nav id="navbar" className="navbar navbar-light bg-faded">
      <button className="navbar-toggler hidden-sm-up" type="button"
              data-toggle="collapse" data-target="#navbar-header"
              aria-controls="navbar-header">&#9776;</button>
      <div className="collapse navbar-toggleable-xs" id="navbar-header">
        <ul className="nav navbar-nav">
        {
          Routes.map((route) => (
            <li key={route.path} className="nav-item active">
              <Link className="nav-link" to={route.path}>{route.title}</Link>
            </li>
          ))
        }
        </ul>
      </div>
    </nav>
    <main id="content">{children}</main>
  </div>
)

export const App = createApp(
  {}, // <- reducers
  {}  // <- initial state
)

export default App
