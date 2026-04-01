from scapy.all import rdpcap

def stream_pcap(file_path):
    packets = rdpcap(file_path)

    for pkt in packets:
        yield {
            "src_port": pkt.sport if hasattr(pkt, 'sport') else 0,
            "dst_port": pkt.dport if hasattr(pkt, 'dport') else 0,
            "seq": getattr(pkt, "seq", 0),
            "ack": getattr(pkt, "ack", 0),
            "inter_arrival_time": 0.001,  # placeholder
            "rolling_loss_rate": 0.0,     # you can compute later
            "retransmission": 0
        }