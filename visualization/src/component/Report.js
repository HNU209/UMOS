import {useEffect, useState } from 'react';
import '../css/report.css'
import { Chart as ChartJS, ArcElement, Tooltip, Legend, CategoryScale, registerables  } from "chart.js";
import { Pie, Bar } from 'react-chartjs-2';
import legendImg from '../img/legend.png';

ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, ...registerables);

function getHistData(data, time, arrLength, range) {
    const arr = new Array(arrLength+1).fill(0);
    Object.values(data).forEach((v) => {
        const timestamp = v.timestamp
        const [start, end] = timestamp.length === 2 ? timestamp : [timestamp[0], timestamp[0]];
        if ((time >= start) && (time <= end)) {
            const timedelta = parseInt((end - start) / 10)
            const timeIndex = timedelta ? timedelta >= 6 ? 6 : timedelta : 0
            arr.splice(timeIndex, 1, arr[timeIndex] + 1)
        }
    })
    return arr
}

export default function Report(props){
    const result = props.result
    const time = props.time

    const range = props.range * 2;
    const maxWaitTime = props.maxWaitTime * 2;
    const arrLength = parseInt(maxWaitTime / range)
    const ps = props.ps
    const [histData, setHistData] = useState();
    const reducer = (accumulator, curr) => accumulator + curr;
    const [histDataPersent, setHistDataPersent] = useState();

    useEffect(() => {
        const updateData = getHistData(ps, time, arrLength, range);
        if (histData !== updateData) {
            setHistData(updateData)
            const totalDataSum = updateData.reduce(reducer)

            const arr = [];
            for (let i of updateData) {
                arr.push(i / totalDataSum * 100)
            }
            setHistDataPersent(arr)
        }
    }, [time])

    const driveTaxiNum = props.driveTaxiNum // 운행중인 택시
    const emptyTaxiNum = props.emptyTaxiNum // 빈 택시
    // const failPsCumsum = props.failPsCumsum // 실패 승객
    // const waitPsNum = props.waitPsNum // 대기 승객

    const data1 = {
        labels: ['현재 운행중인 택시', '현재 비어있는 택시'],
        datasets: [
          {
            label: 'taxi',
            data: [driveTaxiNum, emptyTaxiNum],
            
            backgroundColor: [
                'rgba(253, 231, 37, 0.5)',
                'rgba(94, 201, 98, 0.5)'
            ],
            borderColor: [
                'rgba(253, 231, 37, 0.5)',
                'rgba(94, 201, 98, 0.5)'
            ],
            borderWidth: 0,
          },
        ],
      };

    const data2 = {
        labels: Array.apply(null, Array(arrLength+1)).map(function (_, i) {return String(i*range);}),
        datasets: [
          {
            label: 'passenger (%)',
            data: histDataPersent,
            borderColor: 'blue',
            Color: 'blue',
            fill: true,
            borderWidth: 0,
            barPercentage: 1,
            categoryPercentage: 1,
            hoverBackgroundColor: "darkgray",
            barThickness: "flex",
            backgroundColor: [
                'rgba(0, 0, 255, 0.5)'
            ]
          },
        ],
    };

    const options1= {
        maintainAspectRatio: false,
        responsive: true,
        plugins: {
            legend: {
                display: true,
                labels: {
                    color: 'rgb(255, 255, 255)'
                }
            },
        }
    }
    const options2= {
        maintainAspectRatio: false,
        responsive: true,
        plugins: {
            legend: {
                display: true,
                labels: {
                    color: 'rgb(255, 255, 255)'
                }
            },
        },
        scales: {
            x: {
                ticks: {
                    color: 'white'
                }
                ,
                title: {
                    display: true,
                    align: 'center',
                    text: '대기시간(분)',
                    color: 'rgb(255, 255, 255)'
                }
            },
            y: {
                suggestedMin: 0,
                suggestedMax: 100,
                ticks: {
                    stepSize: 20,
                    color: 'white'
                }
            }
        }
    }

    return(
        <div className="report-container">
            <h1 className='report-header'>REPORT</h1>
            <div className='chart-container'>
                <div>
                    <Pie className="chart1" data={data1} options={options1}></Pie>
                </div>
                <div>
                    <Bar className="chart2" data={data2} options={options2}></Bar>
                </div>
            </div>
            <div className='legend-container'>
                <img className='legend' src={legendImg} />
                <div className='color-scale-bar'>
                    <p className='color-scale-bar-title'>호출 승객 대기 시간</p>
                    <div className='bar'></div>
                    <div className='label'>
                        <p>0분</p>
                        <p>{maxWaitTime}분</p>
                    </div>
                </div>
            </div>
        </div>
    )
}