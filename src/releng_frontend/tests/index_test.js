import React from 'react'
import chai from 'chai'
import chaiEnzyme from 'chai-enzyme'
import chaiImmutable from 'chai-immutable';
import { Link } from 'react-router'
import { fromJS } from 'immutable';
import { shallow } from 'enzyme'

import { Layout, routes } from './../src/layout';
import app, { initialState, reducers } from './../src/index';

const expect = chai.expect;

chai.use(chaiImmutable);
chai.use(chaiEnzyme())

describe('<Layout />', () => {

  it('renders nav and main element', () => {
    const wrapper = shallow(<Layout/>);
    expect(wrapper.find('nav')).to.have.length(1);
    expect(wrapper.find('#content')).to.have.length(1);
  });

  it('renders <Link/> elements for all routes', () => {
    const wrapper = shallow(<Layout/>);
    expect(wrapper.find(Link)).to.have.length(routes.count());
  });

  it('test that initialState is our current state (without routing)', () => {
    expect(app.store.getState().delete('routing')).to.equal(fromJS(initialState));
  });

});
