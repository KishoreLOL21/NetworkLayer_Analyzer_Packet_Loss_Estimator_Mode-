#!/bin/bash

LOSSES=(0 5 10 15 20)

for LOSS in "${LOSSES[@]}"
do
    echo "Running scenario with LOSS = $LOSS%"

    sudo mn -c > /dev/null 2>&1

    sudo mn --topo single,2 --link tc,bw=10,delay=10ms << EOF

    h2 iperf -s -u &
    sleep 2

    h1 tc qdisc add dev h1-eth0 root netem loss ${LOSS}%

    h1 tcpdump -i h1-eth0 -w capture_loss${LOSS}.pcap &
    TCPDUMP_PID=\$!
    sleep 2

    h1 iperf -c h2 -u -b 10M -t 60

    sleep 2
    kill \$TCPDUMP_PID
    sleep 2

    exit
EOF

    echo "Checking packet count..."
    tshark -r capture_loss${LOSS}.pcap | wc -l
    echo ""

done

sudo mn -c
echo "All scenarios completed successfully."
