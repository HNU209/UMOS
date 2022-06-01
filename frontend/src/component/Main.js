import {useEffect, useReducer, useState } from 'react';
import Trip from './Trip'
import Report from './Report'
import '../css/main.css'

function timeToData(data, time) {
    const t = Math.floor(time - 360)
    return data[t]
}

export default function Main(props){
    const [time, setTime] = useState(0);
    const minTime = 420;
    const maxTime = 1440;

    const trip = props.trip
    const empty = props.empty
    const ps = props.ps
    const result = props.result

    const [driveTaxiNum, setDriveTaxiNum] = useState();
    const [emptyTaxiNum, setEmptyTaxiNum] = useState();
    const [failPsCumsum, setFailPsCumsum] = useState();
    const [waitPsNum, setWaitPsNum] = useState();

    useEffect(() => {
        setDriveTaxiNum(timeToData(result.driving_taxi_num, time))
        setEmptyTaxiNum(timeToData(result.empty_taxi_num, time))
        setFailPsCumsum(timeToData(result.fail_passenger_cumsum, time))
        setWaitPsNum(timeToData(result.waiting_passenger_num, time))
    }, [time])

    return(
        <div className="container">
            <Trip trip={trip} empty={empty} ps={ps} setTime={setTime}
            minTime={minTime} maxTime={maxTime}/>
            <Report time={time} ps={ps} result={result}
            driveTaxiNum={driveTaxiNum} emptyTaxiNum={emptyTaxiNum} failPsCumsum={failPsCumsum} waitPsNum={waitPsNum}></Report>
        </div>
    )
}