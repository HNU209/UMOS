import React, { useState, useEffect } from 'react';
import { StaticMap } from 'react-map-gl';
import { AmbientLight, PointLight, LightingEffect } from '@deck.gl/core';
import DeckGL from '@deck.gl/react';
import { PolygonLayer, ScatterplotLayer, IconLayer } from '@deck.gl/layers';
import { TripsLayer } from '@deck.gl/geo-layers';
import Slider from '@mui/material/Slider';
import '../css/trip.css'

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
  longitude: 126.9779900,
  latitude: 37.566535,
  zoom: 10.9,
  minZoom: 5,
  maxZoom: 16,
  pitch: 50,
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

function currentData(time, data) {
  const arr = [];
  Object.values(data).forEach(v => {
    const path = v.path;
    const timestamp = v.timestamp;
    const [start, end] = timestamp.length === 2 ? timestamp : [timestamp[0], timestamp[0]];

    if ((time >= start) && (time <= end)) {
        arr.push(path)
    }
  })
  return (arr)
}

function getPsColor(time, data, range, maxWaitTime) {
  const indexRange = parseInt(maxWaitTime / range)
  const arr = [];
  Object.values(data).forEach(v => {
    const path = v.path;
    const timestamp = v.timestamp;
    const [start, end] = timestamp.length === 2 ? timestamp : [timestamp[0], timestamp[0]];
    
    if ((time >= start) && (time <= end)) {
      const colorIndex = parseInt((time - start) / range)
      const colorR = Number(255 - ((255 / indexRange) * colorIndex))
      const color = colorR >= 0 && colorR <= 255 ? colorR : 0

      const RGB = v.fail === 1 ? [255, color*2, 0] : [255, color, 0]
      arr.push({
        'path': path,
        'color': RGB,
      })
    }
  })
  return arr
}

function renderLayers(props) {
  const theme = DEFAULT_THEME;
  const time = props.time;
  const trips = props.trip;
  const empty = props.empty;
  const ps = props.ps;
  const range = props.range;
  const maxWaitTime = props.maxWaitTime;

  const emptyArr = currentData(time, empty);
  const psArr = getPsColor(time, ps, range, maxWaitTime);

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
      trailLength: 1.5,
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
      getPosition: (d) => d.path,
      getColor: d => d.color,
      opacity: 0.9,
      pickable: false,
      radiusMinPixels: 3,
      radiusMaxPixels: 30,
    }),
  ];
}

export default function Trip(props) {
  const minTime = props.minTime;
  const maxTime = props.maxTime;
  const range = props.range;
  const maxWaitTime = props.maxWaitTime;

  const animationSpeed = 4;
  const time = props.time;
  
  const trip = props.trip
  const empty = props.empty
  const ps = props.ps

  const driveTaxiNum = props.driveTaxiNum
  const emptyTaxiNum = props.emptyTaxiNum
  const successPsCumsum = props.successPsCumsum
  const failPsCumsum = props.failPsCumsum
  const waitPsNum = props.waitPsNum
  const meanWaitTime = props.meanWaitTime

  const [animationFrame, setAnimationFrame] = useState('');
  const viewState = undefined;
  const mapStyle = 'mapbox://styles/spear5306/ckzcz5m8w002814o2coz02sjc';

  function animate() {
    props.setTime(time => {
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
    props.setTime(time)
  }, [time])

  useEffect(() => {
    animate()
    return () => window.cancelAnimationFrame(animationFrame);
  }, [])

  function SliderChange(value) {
    props.setTime(value.target.value)
  }

  return (
    <div className="trip-container" style={{position:'relative'}}>
      <DeckGL
        layers={renderLayers({'trip':trip, 'empty':empty, 'ps':ps, 'time':time, 'range':range, 'maxWaitTime':maxWaitTime})}
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
      </DeckGL>
      <h1 className="time">
        TIME : {(String(parseInt(Math.round(time) / 60) % 24).length === 2) ? parseInt(Math.round(time) / 60) % 24 : '0'+String(parseInt(Math.round(time) / 60) % 24)} : {(String(Math.round(time) % 60).length === 2) ? Math.round(time) % 60 : '0'+String(Math.round(time) % 60)}
      </h1>
      <div className='subtext'>
        <div>- 현재 운행중인 택시&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;: {driveTaxiNum}대</div>
        <div>- 현재 비어있는 택시&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;: {emptyTaxiNum}대</div>
        <div>- 배차 성공 누적 승객 수&nbsp;: {successPsCumsum}명</div>
        <div>- 배차 실패 누적 승객 수&nbsp;: {failPsCumsum}명</div>
        <div>- 탑승 대기 승객 수&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;: {waitPsNum}명</div>
        <div>- 평균 대기 시간&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;: {meanWaitTime}분</div>
      </div>
      <Slider id="slider" value={time} min={minTime} max={maxTime} onChange={SliderChange} track="inverted"/>
    </div>
  );
}