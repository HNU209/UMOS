import React, { useState, useEffect } from 'react';
import { StaticMap } from 'react-map-gl';
import { AmbientLight, PointLight, LightingEffect } from '@deck.gl/core';
import DeckGL from '@deck.gl/react';
import { PolygonLayer, ScatterplotLayer, IconLayer } from '@deck.gl/layers';
import { TripsLayer } from '@deck.gl/geo-layers';
import Slider from '@mui/material/Slider';

const MAPBOX_TOKEN = `pk.eyJ1Ijoic3BlYXI1MzA2IiwiYSI6ImNremN5Z2FrOTI0ZGgycm45Mzh3dDV6OWQifQ.kXGWHPRjnVAEHgVgLzXn2g`; // eslint-disable-line

const ambientLight = new AmbientLight({
  color: [255, 255, 255],
  intensity: 1.0,
});

const pointLight = new PointLight({
  color: [255, 255, 255],
  intensity: 2.0,
  position: [-74.05, 40.7, 8000],
});

const lightingEffect = new LightingEffect({ ambientLight, pointLight });

const material = {
  ambient: 0.1,
  diffuse: 0.6,
  shininess: 32,
  specularColor: [60, 64, 70],
};

const DEFAULT_THEME = {
  buildingColor: [74, 80, 87],
  trailColor0: [253, 128, 93],
  trailColor1: [23, 184, 190],
  material,
  effects: [lightingEffect],
};

const INITIAL_VIEW_STATE = {
  longitude: 126.9779692,
  latitude: 37.566535,
  zoom: 9.5,
  pitch: 30,
  bearing: 0,
};

const landCover = [
  [
    [-74.0, 40.7],
    [-74.02, 40.7],
    [-74.02, 40.72],
    [-74.0, 40.72],
  ],
];

const ICON_MAPPING = {
  marker: {x: 0, y: 0, width: 128, height: 128, mask: true}
};

function restructureData(time, data) {
  const Arr = [];

  Object.values(data).forEach(v => {
    const path = v.path;
    const timestamp = v.timestamp;
    const [start, end] = timestamp.length === 2 ? timestamp : [timestamp[0], timestamp[0]];

    if ((time >= start) & (time <= end)) {
      Arr.push(path);
    }
  })

  return (Arr)
}

function renderLayers(props) {
  const theme = DEFAULT_THEME;
  const time = props.time;
  const trips = props.trip;
  const empty = props.empty;
  const ps = props.ps;

  const emptyArr = restructureData(time, empty);
  const psArr = restructureData(time, ps);

  return [
    new PolygonLayer({
      id: 'ground',
      data: landCover,
      getPolygon: (f) => f,
      stroked: false,
      getFillColor: [0, 0, 0, 0],
    }),
    new TripsLayer({
      id: 'trips',
      data: trips,
      getPath: (d) => d.path,
      getTimestamps: (d) => d.timestamps,
      getColor: (d) =>
        d.vendor === 0 ? theme.trailColor0 : theme.trailColor1,
      opacity: 0.3,
      widthMinPixels: 5,
      lineJointRounded: false,
      trailLength: 0.5,
      currentTime: time,
      shadowEnabled: false,
    }),
    new ScatterplotLayer({
      id: 'scatterplot',
      data: emptyArr,
      getPosition: (d) => [d[0], d[1]],
      getFillColor: (d) => [255, 255, 255],
      getRadius: (d) => 50,
      opacity: 0.9,
      pickable: false,
      radiusMinPixels: 3,
      radiusMaxPixels: 30,
    }),
    new IconLayer({
      id: 'icon-layer',
      data: psArr,
      sizeScale: 15,
      iconAtlas: 'https://raw.githubusercontent.com/visgl/deck.gl-data/master/website/icon-atlas.png',
      iconMapping: ICON_MAPPING,
      getIcon: (d) => 'marker',
      getSize: d => 1,
      getPosition: (d) => [d[0], d[1]],
      getColor: d => [255, 255, 0],
      opacity: 0.9,
      pickable: false,
      radiusMinPixels: 3,
      radiusMaxPixels: 30,
    }),
  ];
}

export default function Main(props) {
  const minTime = 420;
  const maxTime = 1440;
  const animationSpeed = 2;
  const [time, setTime] = useState(minTime);
  const trip = props.trip
  const empty = props.empty
  const ps = props.ps
  const [animationFrame, setAnimationFrame] = useState('');
  const viewState = undefined;
  const mapStyle = 'mapbox://styles/spear5306/ckzcz5m8w002814o2coz02sjc';

  function animate() {
    setTime(time => {
      if (time > maxTime) {
        return minTime
      } else {
        return time + (0.01) * animationSpeed
      }
    })
    const af = window.requestAnimationFrame(animate);
    setAnimationFrame(af)
  }

  useEffect(() => {
    animate()
    return () => window.cancelAnimationFrame(animationFrame);
  }, [])

  function SliderChange(value) {
    setTime(value.target.value)
  }

  return (
    <div>
      <DeckGL
        layers={renderLayers({'trip':trip, 'empty':empty, 'ps':ps, 'time':time})}
        effects={DEFAULT_THEME.effects}
        viewState={viewState}
        controller={true}
        initialViewState={INITIAL_VIEW_STATE}
      >
        <StaticMap
          mapStyle={mapStyle}
          preventStyleDiffing={true}
          mapboxApiAccessToken={MAPBOX_TOKEN}
        />
        <h1 style={{ color: 'red' }}>
          TIME : {(String(parseInt(Math.round(time) / 60) % 24).length === 2) ? parseInt(Math.round(time) / 60) % 24 : '0'+String(parseInt(Math.round(time) / 60) % 24)} : {(String(Math.round(time) % 60).length === 2) ? Math.round(time) % 60 : '0'+String(Math.round(time) % 60)}
        </h1>
      </DeckGL>
      <Slider id="slider" value={time} min={minTime} max={maxTime} onChange={SliderChange} track="inverted" aria-label="Default" valueLabelDisplay="auto" />
    </div>
  );
}