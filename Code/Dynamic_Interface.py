import pyshark
import time
from orchestrator.orchestrator import AgentOrchestrator

INTERFACE = "Wi-Fi"   

MAX_PACKETS = 50

def extract_packet_features(pkt, prev_state):
    try:
        # Ensure TCP + IP layers exist
        if not hasattr(pkt, "tcp") or not hasattr(pkt, "ip"):
            return None

        tcp = pkt.tcp
        ip = pkt.ip

        def safe_int(val, default=0):
            try:
                return int(val)
            except:
                return default

        seq = safe_int(getattr(tcp, "seq", 0))
        ack = safe_int(getattr(tcp, "ack", 0))
        tcp_len = safe_int(getattr(tcp, "len", 0))
        src_port = safe_int(getattr(tcp, "srcport", 0))
        dst_port = safe_int(getattr(tcp, "dstport", 0))

        timestamp = float(pkt.sniff_timestamp)

        last_time = prev_state.get("last_time")

        if last_time is None:
            iat = 0.0
        else:
            iat = timestamp - last_time

        seq_delta = seq - prev_state.get("last_seq", seq)
        ack_delta = ack - prev_state.get("last_ack", ack)

        prev_state["last_time"] = timestamp
        prev_state["last_seq"] = seq
        prev_state["last_ack"] = ack

        loss_flag = 1 if hasattr(tcp, "analysis_retransmission") else 0

        prev_state["loss_window"].append(loss_flag)

        if len(prev_state["loss_window"]) > 10:
            prev_state["loss_window"].pop(0)

        rolling_loss_rate = (
            sum(prev_state["loss_window"]) / len(prev_state["loss_window"])
            if prev_state["loss_window"]
            else 0.0
        )

        packet = {
            "src_port": src_port,
            "dst_port": dst_port,
            "seq": seq,
            "ack": ack,
            "inter_arrival_time": iat,
            "rolling_loss_rate": rolling_loss_rate,
            "retransmission": loss_flag,
            "payload_len": tcp_len,
        }

        return packet

    except Exception as e:
        print("⚠️ Feature extraction error:", e)
        return None


def run_live_mode(orchestrator):
    print("\n📡 LIVE CAPTURE STARTED...\n")

    try:
        cap = pyshark.LiveCapture(
            interface=INTERFACE,
            display_filter="tcp"
        )
    except Exception as e:
        print("❌ Failed to start capture:", e)
        return

    prev_state = {
        "last_time": None,
        "last_seq": 0,
        "last_ack": 0,
        "loss_window": []
    }

    count = 0

    try:
        for pkt in cap.sniff_continuously():

            packet = extract_packet_features(pkt, prev_state)

            if packet is None:
                continue

            print(f"\n📦 Packet #{count + 1}")
            # print("Raw Features:", packet)

            decision = orchestrator.run(packet)

            print("🎯 FINAL DECISION:", decision)

            count += 1

            if count >= MAX_PACKETS:
                print("\n🛑 Stopping capture (limit reached)")
                break

    except KeyboardInterrupt:
        print("\n🛑 Capture stopped by user")

    except Exception as e:
        print("❌ Runtime error:", e)


if __name__ == "__main__":
    orchestrator = AgentOrchestrator()

    run_live_mode(orchestrator)