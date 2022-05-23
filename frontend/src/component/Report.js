import {useEffect, useState } from 'react';
import '../css/report.css'

export default function Report(props){
    const result = props.result
    const time = props.time

    const driveTaxiNum = props.driveTaxiNum
    const emptyTaxiNum = props.emptyTaxiNum
    const failPsCumsum = props.failPsCumsum
    const waitPsNum = props.waitPsNum

    return(
        <div className="report-container">
            <h1 className="time" style={{ color: 'red' }}>
                TIME : {(String(parseInt(Math.round(time) / 60) % 24).length === 2) ? parseInt(Math.round(time) / 60) % 24 : '0'+String(parseInt(Math.round(time) / 60) % 24)} : {(String(Math.round(time) % 60).length === 2) ? Math.round(time) % 60 : '0'+String(Math.round(time) % 60)}
            </h1>
            <div className='report-printing'>
                <div>- 현재 운행중인 택시     : {driveTaxiNum}대</div>
                <div>- 현재 비어있는 택시     : {emptyTaxiNum}대</div>
                <div>- 배차 실패 누적 승객 수 : {failPsCumsum}명</div>
                <div>- 배차 대기 승객 수      : {waitPsNum}명</div>
            </div>
        </div>
    )
}