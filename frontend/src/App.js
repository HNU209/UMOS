import './css/App.css';
import Main from './component/Main';
import Splash from './component/Splash';
import { useEffect, useState } from 'react';

const axios = require('axios');

function getData(server, type){
  const url = `${server}/data/${type}`
  const response = axios.get(url);
  return response.then(res => res.data)
}

export default function App() {
  const server = 'http://20.200.200.212:5000'
  const [load, setLoad] = useState(false);
  const [trip, setTrip] = useState();
  const [empty, setEmpty] = useState();
  const [ps, setPs] = useState();
  const [result, setResult] = useState();
  
  useEffect(() => {
    async function getFetchData() {
      const trip = await getData(server, 'trip')
      const empty = await getData(server, 'empty')
      const ps = await getData(server, 'ps')
      const result = await getData(server, 'result')

      if (trip && empty && ps) {
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