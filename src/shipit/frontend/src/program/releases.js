/* TODO: explain what this file is about
 *
 */
import withLayout from './../layout';

export const Program = ({
  init: [{ text: 'Releases' }],
  update: (message, model) => model,
  view: model => <h1>{model.text}</h1>,
});

export default flags => withLayout(flags, Program);
