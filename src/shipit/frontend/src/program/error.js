/* TODO: explain what this file is about
 *
 */

import withLayout from './../layout';

export default ({
  init: [{ text: 'ERROR' }],
  update: (message, model) => model,
  view: model => <p>{model.text}</p>,
});

export default flags => withLayout(flags, Program);
