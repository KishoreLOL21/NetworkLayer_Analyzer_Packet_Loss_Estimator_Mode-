from orchestrator.orchestrator import AgentOrchestrator
import pyshark
import pandas as pd

PCAP_FILE = "../Data/Test.pcapng"


# ==================================================
# PARSE PCAP → EXTRACT ALL REQUIRED FEATURES
# ==================================================
def parse_pcap(pcap_file):
    print(f"\n[*] Parsing PCAP: {pcap_file}")

    cap = pyshark.FileCapture(pcap_file, display_filter="tcp")

    def to_int(val):
        try:
            return int(val)
        except:
            return 1 if str(val).lower() == "true" else 0

    records = []

    for pkt in cap:
        try:
            tcp = pkt.tcp
            ip = pkt.ip

            record = {
                "ip_len": int(ip.len),

                "tcp_srcport": int(tcp.srcport),
                "tcp_dstport": int(tcp.dstport),
                "tcp_seq": int(tcp.seq),
                "tcp_ack": int(tcp.ack),
                "tcp_len": int(tcp.len),
                "tcp_window_size": int(tcp.window_size_value),

                "flag_syn": to_int(tcp.flags_syn),
                "flag_ack": to_int(tcp.flags_ack),
                "flag_fin": to_int(tcp.flags_fin),
                "flag_rst": to_int(tcp.flags_reset),
                "flag_push": to_int(tcp.flags_push),

                "frame_time_delta": float(pkt.frame_info.time_delta),
                "frame_time_epoch": float(pkt.frame_info.time_epoch),
            }

            records.append(record)

        except AttributeError:
            continue

    cap.close()

    df = pd.DataFrame(records)

    if df.empty:
        raise ValueError("❌ No TCP packets found")

    # Normalize time
    df["frame_time_epoch"] -= df["frame_time_epoch"].min()

    return df


# ==================================================
# FEATURE ENGINEERING (MATCH TRAINING PIPELINE)
# ==================================================
def engineer_features(df):
    df = df.sort_values("frame_time_epoch").reset_index(drop=True)

    df["iat"] = df["frame_time_epoch"].diff().fillna(0)
    df["seq_delta"] = df["tcp_seq"].diff().fillna(0)
    df["ack_delta"] = df["tcp_ack"].diff().fillna(0)

    df["rolling_mean_len"] = df["tcp_len"].rolling(5, min_periods=1).mean()
    df["rolling_std_len"] = df["tcp_len"].rolling(5, min_periods=1).std().fillna(0)

    # Initially 0 → will update dynamically during inference
    df["rolling_loss_rate"] = 0.0

    return df


# ==================================================
# RUN AGENT + UPDATE ROLLING LOSS
# ==================================================
def run_pcap(orchestrator, df):
    print("\n📡 Running Agentic AI...\n")

    total_packets = 0
    predicted_loss = 0

    loss_history = []

    for i, row in df.iterrows():

        # Update rolling loss dynamically
        rolling_loss = (
            sum(loss_history[-10:]) / len(loss_history[-10:])
            if len(loss_history) > 0 else 0
        )

        pkt = {
            "ip_len": row["ip_len"],
            "src_port": row["tcp_srcport"],
            "dst_port": row["tcp_dstport"],
            "seq": row["tcp_seq"],
            "ack": row["tcp_ack"],
            "payload_len": row["tcp_len"],
            "window_size": row["tcp_window_size"],

            "flag_syn": row["flag_syn"],
            "flag_ack": row["flag_ack"],
            "flag_fin": row["flag_fin"],
            "flag_rst": row["flag_rst"],
            "flag_push": row["flag_push"],

            "inter_arrival_time": row["iat"],
            "seq_delta": row["seq_delta"],
            "ack_delta": row["ack_delta"],
            "rolling_mean_len": row["rolling_mean_len"],
            "rolling_std_len": row["rolling_std_len"],
            "rolling_loss_rate": rolling_loss,
        }

        decision = orchestrator.run(pkt)

        is_loss = 1 if str(decision).lower() in ["loss", "lost", "1", "true"] else 0

        loss_history.append(is_loss)
        predicted_loss += is_loss
        total_packets += 1

        print(f"Packet {i+1}: {decision}")

    loss_rate = (predicted_loss / total_packets) * 100 if total_packets else 0

    print("\n==============================")
    print(f"Total TCP Packets      : {total_packets}")
    print(f"Predicted Lost Packets : {predicted_loss}")
    print(f"📉 Loss Rate           : {loss_rate:.4f}%")
    print("==============================\n")


if __name__ == "__main__":
    orchestrator = AgentOrchestrator()

    df = parse_pcap(PCAP_FILE)
    df = engineer_features(df)

    run_pcap(orchestrator, df)