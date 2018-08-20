import { Alert } from 'reactstrap';

export const notAskedView = (children = 'Just about to start loading...') => () => (
  <div className="show-after-1s">{children}</div>
);

export const loadingView = () => {
  const outerStyle = {
    width: '100%',
    height: '100px',
    background: 'transparent',
  };
  const innerStyle = {
    width: '100%',
    height: '100%',
    margin: '0',
    padding: '0',
  };
  return (
    <div style={outerStyle}>
      <div style={innerStyle}>
        <svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg" xmlnsXlink="http://www.w3.org/1999/xlink" viewBox="0 0 100 100" preserveAspectRatio="xMidYMid">
          <g transform="translate(12.5 50)">
            <circle cx="0" cy="0" r="5" fill="#4d4f53">
              <animateTransform attributeName="transform" type="scale" begin="-0.42857142857142855s" calcMode="spline" keySplines="0.3 0 0.7 1;0.3 0 0.7 1" values="0;1;0" keyTimes="0;0.5;1" dur="1s" repeatCount="indefinite" />
            </circle>
          </g>
          <g transform="translate(25 50)">
            <circle cx="0" cy="0" r="5" fill="#4d4f53">
              <animateTransform attributeName="transform" type="scale" begin="-0.35714285714285715s" calcMode="spline" keySplines="0.3 0 0.7 1;0.3 0 0.7 1" values="0;1;0" keyTimes="0;0.5;1" dur="1s" repeatCount="indefinite" />
            </circle>
          </g>
          <g transform="translate(37.5 50)">
            <circle cx="0" cy="0" r="5" fill="#4d4f53">
              <animateTransform attributeName="transform" type="scale" begin="-0.2857142857142857s" calcMode="spline" keySplines="0.3 0 0.7 1;0.3 0 0.7 1" values="0;1;0" keyTimes="0;0.5;1" dur="1s" repeatCount="indefinite" />
            </circle>
          </g>
          <g transform="translate(50 50)">
            <circle cx="0" cy="0" r="5" fill="#4d4f53">
              <animateTransform attributeName="transform" type="scale" begin="-0.21428571428571427s" calcMode="spline" keySplines="0.3 0 0.7 1;0.3 0 0.7 1" values="0;1;0" keyTimes="0;0.5;1" dur="1s" repeatCount="indefinite" />
            </circle>
          </g>
          <g transform="translate(62.5 50)">
            <circle cx="0" cy="0" r="5" fill="#4d4f53">
              <animateTransform attributeName="transform" type="scale" begin="-0.14285714285714285s" calcMode="spline" keySplines="0.3 0 0.7 1;0.3 0 0.7 1" values="0;1;0" keyTimes="0;0.5;1" dur="1s" repeatCount="indefinite" />
            </circle>
          </g>
          <g transform="translate(75 50)">
            <circle cx="0" cy="0" r="5" fill="#4d4f53">
              <animateTransform attributeName="transform" type="scale" begin="-0.07142857142857142s" calcMode="spline" keySplines="0.3 0 0.7 1;0.3 0 0.7 1" values="0;1;0" keyTimes="0;0.5;1" dur="1s" repeatCount="indefinite" />
            </circle>
          </g>
          <g transform="translate(87.5 50)">
            <circle cx="0" cy="0" r="5" fill="#4d4f53">
              <animateTransform attributeName="transform" type="scale" begin="0s" calcMode="spline" keySplines="0.3 0 0.7 1;0.3 0 0.7 1" values="0;1;0" keyTimes="0;0.5;1" dur="1s" repeatCount="indefinite" />
            </circle>
          </g>
        </svg>
      </div>
    </div>
  );
};

export const failureView = error => (
  <Alert color="danger">
    <h4 className="alert-heading">{error.name}</h4>
    <p>{error.message}</p>
  </Alert>
);
