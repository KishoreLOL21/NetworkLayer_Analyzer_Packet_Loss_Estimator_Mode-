from orchestrator.orchestrator import AgentOrchestrator

try:
    from stream.pcap_stream import stream_pcap
    STREAM_AVAILABLE = True
except ImportError:
    STREAM_AVAILABLE = False

MODE = "test"      
PCAP_FILE = "../Data/capture_loss10.pcap"

test_packets = [

    # NO LOSS
    {
        "dst_port": 80, "inter_arrival_time": 0.0015, "rolling_loss_rate": 0.0,
        "duplicate_ack_count": 0, "seq": 1000, "duplicate_ack": 0,
        "jitter": 0.0003, "ack": 1000, "rtt_estimate": 0.003,
        "retransmission": 0, "retransmission_rate": 0.0,
        "lost_segment": 0, "src_port": 5000, "timestamp": 1.771739e9
    },
    {
        "dst_port": 443, "inter_arrival_time": 0.0025, "rolling_loss_rate": 0.0,
        "duplicate_ack_count": 0, "seq": 2500, "duplicate_ack": 0,
        "jitter": 0.0006, "ack": 2500, "rtt_estimate": 0.005,
        "retransmission": 0, "retransmission_rate": 0.0,
        "lost_segment": 0, "src_port": 5001, "timestamp": 1.771739e9
    },

    # BORDERLINE
    {
        "dst_port": 80, "inter_arrival_time": 0.01, "rolling_loss_rate": 0.2,
        "duplicate_ack_count": 1, "seq": 20000, "duplicate_ack": 0,
        "jitter": 0.005, "ack": 20000, "rtt_estimate": 0.02,
        "retransmission": 0, "retransmission_rate": 0.1,
        "lost_segment": 0, "src_port": 5002, "timestamp": 1.771739e9
    },
    {
        "dst_port": 443, "inter_arrival_time": 0.015, "rolling_loss_rate": 0.25,
        "duplicate_ack_count": 1, "seq": 22000, "duplicate_ack": 0,
        "jitter": 0.006, "ack": 22000, "rtt_estimate": 0.03,
        "retransmission": 0, "retransmission_rate": 0.15,
        "lost_segment": 0, "src_port": 5003, "timestamp": 1.771739e9
    },

    # CLEAR LOSS
    {
        "dst_port": 80, "inter_arrival_time": 0.08, "rolling_loss_rate": 0.6,
        "duplicate_ack_count": 3, "seq": 34813, "duplicate_ack": 1,
        "jitter": 0.02, "ack": 29, "rtt_estimate": 0.25,
        "retransmission": 1, "retransmission_rate": 0.5,
        "lost_segment": 1, "src_port": 5004, "timestamp": 1.771739e9
    },
    {
        "dst_port": 443, "inter_arrival_time": 0.1, "rolling_loss_rate": 0.7,
        "duplicate_ack_count": 4, "seq": 56533, "duplicate_ack": 1,
        "jitter": 0.03, "ack": 29, "rtt_estimate": 0.3,
        "retransmission": 1, "retransmission_rate": 0.6,
        "lost_segment": 1, "src_port": 5005, "timestamp": 1.771739e9
    },

    # EXTREME LOSS
    {
        "dst_port": 80, "inter_arrival_time": 0.15, "rolling_loss_rate": 0.9,
        "duplicate_ack_count": 5, "seq": 113005, "duplicate_ack": 1,
        "jitter": 0.05, "ack": 29, "rtt_estimate": 0.5,
        "retransmission": 1, "retransmission_rate": 0.8,
        "lost_segment": 1, "src_port": 5006, "timestamp": 1.771739e9
    },
    {
        "dst_port": 443, "inter_arrival_time": 0.2, "rolling_loss_rate": 0.95,
        "duplicate_ack_count": 6, "seq": 157893, "duplicate_ack": 1,
        "jitter": 0.06, "ack": 29, "rtt_estimate": 0.6,
        "retransmission": 1, "retransmission_rate": 0.9,
        "lost_segment": 1, "src_port": 5007, "timestamp": 1.771739e9
    }
]


def run_test_mode(orchestrator):
    print("\n🧪 Running TEST MODE\n")

    for i, pkt in enumerate(test_packets, 1):
        print(f"\n------------------ SAMPLE {i} -------------------")

        decision = orchestrator.run(pkt)

        print("🎯 FINAL DECISION:", decision)


def run_stream_mode(orchestrator):
    if not STREAM_AVAILABLE:
        print("⚠️ Streaming module not available. Install scapy & create stream module.")
        return

    print("\n📡 Running STREAM MODE\n")

    try:
        for packet in stream_pcap(PCAP_FILE):
            decision = orchestrator.run(packet)
            print("🎯 FINAL:", decision)

    except KeyboardInterrupt:
        print("\n🛑 Streaming stopped by user")

if __name__ == "__main__":
    orchestrator = AgentOrchestrator()

    if MODE == "test":
        run_test_mode(orchestrator)

    elif MODE == "stream":
        run_stream_mode(orchestrator)

    else:
        print("❌ Invalid MODE. Use 'test' or 'stream'")