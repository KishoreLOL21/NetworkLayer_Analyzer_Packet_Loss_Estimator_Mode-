from orchestrator.orchestrator import AgentOrchestrator

try:
    from stream.pcap_stream import stream_pcap
    STREAM_AVAILABLE = True
except ImportError:
    STREAM_AVAILABLE = False

MODE = "test"
PCAP_FILE = "../Data/capture_loss10.pcap"

test_packets = [

    {
        "src_port": 57126,
        "dst_port": 5001,
        "seq": 1,
        "ack": 1,
        "inter_arrival_time": 0.0012,
        "rolling_loss_rate": 0.3,
        "retransmission": 1,
        "payload_len": 1448
    },

    {
        "src_port": 40208,
        "dst_port": 5001,
        "seq": 97077,
        "ack": 29,
        "inter_arrival_time": 0.512,
        "rolling_loss_rate": 0.6,
        "retransmission": 1,
        "payload_len": 1448
    },

    {
        "src_port": 5001,
        "dst_port": 49096,
        "seq": 0,
        "ack": 1,
        "inter_arrival_time": 0.0100,
        "rolling_loss_rate": 0.8,
        "retransmission": 1,
        "payload_len": 1448
    },

    {
        "src_port": 49096,
        "dst_port": 5001,
        "seq": 34567,
        "ack": 120,
        "inter_arrival_time": 0.25,
        "rolling_loss_rate": 0.7,
        "retransmission": 1,
        "payload_len": 1400
    },

    {
        "src_port": 40192,
        "dst_port": 5001,
        "seq": 88000,
        "ack": 45,
        "inter_arrival_time": 0.15,
        "rolling_loss_rate": 0.9,
        "retransmission": 1,
        "payload_len": 1500
    },
]


def run_test_mode(orchestrator):
    print("\n🧪 Running TEST MODE (ALL LOSS CASES)\n")

    for i, pkt in enumerate(test_packets, 1):
        print(f"\n---------------- SAMPLE {i} -------------------")

        decision = orchestrator.run(pkt)

        print("🎯 FINAL DECISION:", decision)


def run_stream_mode(orchestrator):
    if not STREAM_AVAILABLE:
        print("⚠️ Streaming module not available.")
        return

    print("\n📡 Running STREAM MODE\n")

    try:
        for packet in stream_pcap(PCAP_FILE):
            decision = orchestrator.run(packet)
            print("🎯 FINAL:", decision)

    except KeyboardInterrupt:
        print("\n🛑 Streaming stopped by user")


# ==================================================
# ENTRY POINT
# ==================================================
if __name__ == "__main__":
    orchestrator = AgentOrchestrator()

    if MODE == "test":
        run_test_mode(orchestrator)

    elif MODE == "stream":
        run_stream_mode(orchestrator)

    else:
        print("❌ Invalid MODE")