import {AppRegistry, LogBox} from 'react-native';
import {App} from './src/App';
import {name as appName} from './app.json';
// W3C Media 2.3.2's bundled SliderMetaData omits the unused ref parameter.
// Filter only this vendor warning so it cannot cover calibration pixels.
if (__DEV__) {LogBox.ignoreLogs([
  'forwardRef render functions accept exactly two parameters: props and ref.',
  // RN's generic warning banner covers the sync pulse. Actual warning text
  // stays in device logs; exceptions and playback errors remain visible.
  'Open debugger to view warnings.',
  'Running debug build of JavaScript',
]);}
AppRegistry.registerComponent(appName, () => App);
