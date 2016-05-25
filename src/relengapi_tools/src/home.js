import React from 'react';
import {Link} from 'react-router';
import {routes} from './layout';

const services = routes.keySeq()
  .filter(x => x !== "home")
  .reduce((result, x) => {
      if (result[result.length-1].length === 3) result.push([]);
      result[result.length -1].push(routes.get(x).toJS());
      return result;
    }, [[]]);

export const Home = () => (
  <div>
    <div id="banner-home">
      <div className="container">
        Collection of Release Engineering services.
      </div>
    </div>
    <div className="container">
      <h1>Services</h1>
      {
        services.map((service_row, key) => (
          <div key={"service-row-" + key}  className="row">
            {
              service_row.map((service, key) => (
                <div key={"service-" + key} className="col-sm-4">
                  <Link className="linked-card" to={service.path}>
                      <div className="card card-block">
                        <h3 className="card-title">{service.title || ''}</h3>
                        <p className="card-text">{service.description || ''}</p>
                      </div>
                  </Link>
                </div>
              ))
            }
          </div>
        ))
      }
    </div>
  </div>
)
Home.__name__ = 'Home'
export default Home;
