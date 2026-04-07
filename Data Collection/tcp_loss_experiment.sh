#!/bin/bash

LOSSES=(0 5 10 15 20)

for LOSS in "${LOSSES[@]}"
do
    echo "Running scenario with LOSS = $LOSS%"

    sudo mn -c > /dev/null 2>&1

    sudo mn --topo single,2 --link tc,bw=10,delay=10ms,loss=${LOSS} << EOF

h2 iperf -s &
sleep 2

h1 tcpdump -i h1-eth0 -w capture_loss${LOSS}.pcap &
TCPDUMP_PID=\$!
sleep 2

h1 iperf -c h2 -t 60 -P 5
sleep 2

kill \$TCPDUMP_PID
sleep 2

exit
EOF

    echo "Results for LOSS = $LOSS%"

    TOTAL=$(tshark -r capture_loss${LOSS}.pcap | wc -l)
    RETRANS=$(tshark -r capture_loss${LOSS}.pcap -Y "tcp.analysis.retransmission" | wc -l)

    echo "Total packets: $TOTAL"
    echo "Retransmissions: $RETRANS"

    if [ "$TOTAL" -gt 0 ]; then
        LOSS_RATIO=$(echo "scale=4; $RETRANS / $TOTAL" | bc)
        echo "Estimated Loss Ratio: $LOSS_RATIO"
    fi

    echo ""
done

sudo mn -c
echo "All scenarios completed successfully."
#!/bin/bash

LOSSES=(0 5 10 15 20)

for LOSS in "${LOSSES[@]}"
do
    echo "===================================="
    echo "Running scenario with LOSS = $LOSS%"
    echo "===================================="

    sudo mn -c > /dev/null 2>&1

    sudo mn --topo single,2 --link tc,bw=10,delay=10ms,loss=${LOSS} << EOF

h2 iperf -s &
sleep 2

h1 tcpdump -i h1-eth0 -w capture_loss${LOSS}.pcap &
TCPDUMP_PID=\$!
sleep 2

h1 iperf -c h2 -t 60 -P 5
sleep 2

kill \$TCPDUMP_PID
sleep 2

exit
EOF

    echo "Results for LOSS = $LOSS%"

    TOTAL=$(tshark -r capture_loss${LOSS}.pcap | wc -l)
    RETRANS=$(tshark -r capture_loss${LOSS}.pcap -Y "tcp.analysis.retransmission" | wc -l)

    echo "Total packets: $TOTAL"
    echo "Retransmissions: $RETRANS"

    if [ "$TOTAL" -gt 0 ]; then
        LOSS_RATIO=$(echo "scale=4; $RETRANS / $TOTAL" | bc)
        echo "Estimated Loss Ratio: $LOSS_RATIO"
    fi

    echo ""
done

sudo mn -c
echo "All scenarios completed successfully."
