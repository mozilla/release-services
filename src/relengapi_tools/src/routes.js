import Home from './home';
import BadPenny from './badpenny';
import Clobberer from './clobberer';
import SlaveLoan from './slaveloan';
import Tokens from './tokens';
import ToolTool from './tooltool';
import TreeStatus from './treestatus';


export default [
  { path: '/', title: 'RelengAPI', component: Home },
  { path: '/badpenny', title: 'BadPenny', component: BadPenny },
  { path: Clobberer.__path__, title: Clobberer.__name__, component: Clobberer },
  { path: '/slaveloan', title: 'SlaveLoan', component: SlaveLoan },
  { path: '/tokens', title: 'Tokens', component: Tokens },
  { path: '/tooltool', title: 'ToolTool', component: ToolTool },
  { path: '/treestatus', title: 'TreeStatus', component: TreeStatus }
];
