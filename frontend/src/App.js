import './css/App.css';
import Main from './component/TripComponent';
import Splash from './component/splash';
import { useEffect, useState } from 'react';

function getData(server, type){
  const response = fetch(`${server}/data/${type}`)
  return response.then(res => res.json())
}

export default function App() {
  const server = 'http://20.200.200.212:5000'
  const [load, setLoad] = useState(false);
  const [trip, setTrip] = useState();
  const [empty, setEmpty] = useState();
  const [ps, setPs] = useState();
  
  useEffect(() => {
    async function getFetchData() {
      const trip = await getData(server, 'trip')
      const empty = await getData(server, 'empty')
      const ps = await getData(server, 'ps')
      if (trip && empty && ps) {
        setTrip(trip)
        setEmpty(empty)
        setPs(ps)
        setLoad(true)
      }
    }
    
    getFetchData()
  }, [])
  
  return (
    <div className='App'>
      {load ? <Main trip={trip} empty={empty} ps={ps}/> : <Splash/>}
    </div>
  );
}