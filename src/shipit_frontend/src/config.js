const { CONFIG } = process.env;
export default require(`./configs/${CONFIG}`); // eslint-disable-line import/no-dynamic-require, global-require
