import {configure} from '@testing-library/react-native';

// React Native exports are lazy getters; with a cold transform cache the first
// render compiles them mid-test and can exceed the 1 s waitFor default.
configure({asyncUtilTimeout: 15000});
