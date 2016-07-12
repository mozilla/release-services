import React from 'react';
import {Link} from 'react-router';
import {services} from './layout';

const services_table = services.reduce((result, x) => {
  if (result[result.length-1].length === 3) result.push([]);
  result[result.length -1].push(x.toJS());
  return result;
}, [[]]);

export const Home = () => (
  <div>
    {
      services_table.map((service_row, key) => (
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
)
Home.__name__ = 'Home'
export default Home;
