import {useEffect, useState } from 'react';
import Trip from './Trip'
import Report from './Report'
import '../css/main.css'

function timeToData(data, time) {
    const t = Math.floor(time - 360)
    return data[t]
}

function getMeanWaitTime(data, time) {
    let totalTime = 0;
    let count = 0;
    Object.values(data).forEach(v => {
        const timestamp = v.timestamp
        const [start, end] = timestamp.length === 2 ? timestamp : [timestamp[0], timestamp[0]];

        if (time >= start && time <= end) {
            const deltaTime = end - start
            totalTime += deltaTime
            count += 1
        }
    })
    const t = Math.round(totalTime / count)
    return t ? t : 0
}

export default function Main(props){
    const range = 5;
    const maxWaitTime = 30;
    const minTime = 420;
    const maxTime = 1440;
    const [time, setTime] = useState(minTime);

    const trip = props.trip
    const empty = props.empty
    const ps = props.ps
    const result = props.result

    const [driveTaxiNum, setDriveTaxiNum] = useState(0);
    const [emptyTaxiNum, setEmptyTaxiNum] = useState(0);
    const [successPsCumsum, setSuccessPsCumsum] = useState(0);
    const [failPsCumsum, setFailPsCumsum] = useState(0);
    const [waitPsNum, setWaitPsNum] = useState(0);

    const [meanWaitTime, setMeanWaitTime] = useState(0);

    useEffect(() => {
        setDriveTaxiNum(timeToData(result.driving_taxi_num, time))
        setEmptyTaxiNum(timeToData(result.empty_taxi_num, time))
        setSuccessPsCumsum(timeToData(result.success_passenger_cumsum, time))
        setFailPsCumsum(timeToData(result.fail_passenger_cumsum, time))
        setWaitPsNum(timeToData(result.waiting_passenger_num, time))
        setMeanWaitTime(getMeanWaitTime(ps, time))
    }, [time])

    return(
        <div className="container">
            <Trip trip={trip} empty={empty} ps={ps} time={time} setTime={setTime}
            minTime={minTime} maxTime={maxTime} meanWaitTime={meanWaitTime} range={range} maxWaitTime={maxWaitTime}
            driveTaxiNum={driveTaxiNum} emptyTaxiNum={emptyTaxiNum} successPsCumsum={successPsCumsum} failPsCumsum={failPsCumsum} waitPsNum={waitPsNum}></Trip>
            <Report time={time} ps={ps} result={result} range={range} maxWaitTime={maxWaitTime}
            driveTaxiNum={driveTaxiNum} emptyTaxiNum={emptyTaxiNum} failPsCumsum={failPsCumsum} waitPsNum={waitPsNum}></Report>
        </div>
    )
}