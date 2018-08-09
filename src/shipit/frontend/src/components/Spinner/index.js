import React from 'react';
import { dot, line, back, spin, center } from './styles.css';

// These are roughly in clockwise order starting from the northwest
const Spinner = ({ height = 48, width = 48 }) => (
  <div style={{ textAlign: 'center', marginTop: '2rem' }}>
    <svg height={height} width={width}>
      <g transform="translate(24 24)">
        <g className={spin}>
          <circle cx="0" cy="0" r="23" className={back} />
          <line x1="0" y1="0" x2="-13" y2="-13" className={line} />
          <circle cx="-13" cy="-13" r="2.5" className={dot} />
          <line x1="0" y1="0" x2="-3" y2="-9" className={line} />
          <circle cx="-3" cy="-9" r="2.5" className={dot} />
          <line x1="0" y1="0" x2="3" y2="-17" className={line} />
          <circle cx="3" cy="-17" r="2.5" className={dot} />
          <line x1="0" y1="0" x2="8" y2="-9" className={line} />
          <circle cx="8" cy="-9" r="2.5" className={dot} />
          <line x1="0" y1="0" x2="16" y2="-7" className={line} />
          <circle cx="16" cy="-7" r="2.5" className={dot} />
          <line x1="0" y1="0" x2="13" y2="-1" className={line} />
          <circle cx="13" cy="-1" r="2.5" className={dot} />
          <line x1="0" y1="0" x2="15" y2="5" className={line} />
          <circle cx="15" cy="5" r="2.5" className={dot} />
          <line x1="0" y1="0" x2="8" y2="8" className={line} />
          <circle cx="8" cy="8" r="2.5" className={dot} />
          <line x1="0" y1="0" x2="7" y2="16" className={line} />
          <circle cx="7" cy="16" r="2.5" className={dot} />
          <line x1="0" y1="0" x2="-1" y2="14" className={line} />
          <circle cx="-1" cy="14" r="2.5" className={dot} />
          <line x1="0" y1="0" x2="-8" y2="15" className={line} />
          <circle cx="-8" cy="15" r="2.5" className={dot} />
          <line x1="0" y1="0" x2="-10" y2="7" className={line} />
          <circle cx="-10" cy="7" r="2.5" className={dot} />
          <line x1="0" y1="0" x2="-17" y2="3" className={line} />
          <circle cx="-17" cy="3" r="2.5" className={dot} />
          <line x1="0" y1="0" x2="-10" y2="-4" className={line} />
          <circle cx="-10" cy="-4" r="2.5" className={dot} />
          <circle cx="0" cy="0" r="4" className={center} />
        </g>
      </g>
    </svg>
  </div>
);

export default Spinner;
