/* TODO: explain what this file is about
 *
 */

import layoutView from './../views/layout';

export default {
  init: [{ text: 'Releases' }],
  update: (message, model) => model,
  view: (model, dispatch) => {
    const content = <h1>{model.text}</h1>;
    return layoutView(model, dispatch, content);
  },
};
