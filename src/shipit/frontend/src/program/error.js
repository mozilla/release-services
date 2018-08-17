/* TODO: explain what this file is about
 *
 */

import withLayout from './../layout';

export const Program = ({
  init: [{ text: 'ERROR' }],
  update: (message, model) => model,
  view: model => <p>{model.text}</p>,
});

export default withLayout(Program);
