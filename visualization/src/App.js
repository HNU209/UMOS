import './css/App.css';
import Main from './component/Main';
import Splash from './component/Splash';
import { useEffect, useState } from 'react';

const axios = require('axios');

function getData(type){
  const url = `https://raw.githubusercontent.com/HNU209/UMOS/main/data/${type}.json`
  const response = axios.get(url);
  return response.then(res => res.data)
}

export default function App() {
  const [load, setLoad] = useState(false);
  const [trip, setTrip] = useState();
  const [empty, setEmpty] = useState();
  const [ps, setPs] = useState();
  const [result, setResult] = useState();
  
  useEffect(() => {
    async function getFetchData() {
      const trip = await getData('trip')
      const empty = await getData('empty')
      const ps = await getData('ps')
      const result = await getData('result')

      if (trip && empty && ps && result) {
        setTrip(trip)
        setEmpty(empty)
        setPs(ps)
        setResult(result)
        setLoad(true)
      }
    }

    getFetchData()
  }, [])
  
  return (
    <div className='App'>
      {load ? <Main trip={trip} empty={empty} ps={ps} result={result}/> : <Splash/>}
    </div>
  );
}