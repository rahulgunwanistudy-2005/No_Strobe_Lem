/** VVD forwards port 8765 to the host's dedicated calibration/demo server. */
export const config = {
  catalogBaseUrl: 'http://127.0.0.1:8765',
  catalogPath: '/catalog.json',
  mediaBaseUrl: '/pkg/assets/raw',
  nativeVeilDriver: true,
};
export const disclaimer = 'No Strobe-lem is a viewing aid that reduces flashing according to published broadcast guidelines. It is not a medical device and cannot guarantee that content is safe for every person with photosensitive epilepsy.';
