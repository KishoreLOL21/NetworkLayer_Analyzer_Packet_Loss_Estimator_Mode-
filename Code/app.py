import streamlit as st
import pandas as pd
import pyshark
import time
from orchestrator.orchestrator import AgentOrchestrator
import asyncio

try:
    asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

INTERFACE = "Wi-Fi"
MAX_PACKETS = 100

st.set_page_config(page_title="Agentic AI Packet Analyzer", layout="wide")

st.title("📡 Agentic AI - Real-Time Packet Loss Dashboard")

if "running" not in st.session_state:
    st.session_state.running = False

if "data" not in st.session_state:
    st.session_state.data = []

if "packet_count" not in st.session_state:
    st.session_state.packet_count = 0

col1, col2 = st.columns(2)

with col1:
    if st.button("▶️ Start Capture"):
        st.session_state.running = True

with col2:
    if st.button("⏹️ Stop Capture"):
        st.session_state.running = False

def extract_packet_features(pkt, prev_state):
    try:
        if not hasattr(pkt, "tcp") or not hasattr(pkt, "ip"):
            return None

        tcp = pkt.tcp
        ip = pkt.ip

        def safe_int(val, default=0):
            try:
                return int(val)
            except:
                return default

        # ======================
        # BASIC TCP FEATURES
        # ======================
        seq = safe_int(getattr(tcp, "seq", 0))
        ack = safe_int(getattr(tcp, "ack", 0))
        tcp_len = safe_int(getattr(tcp, "len", 0))
        src_port = safe_int(getattr(tcp, "srcport", 0))
        dst_port = safe_int(getattr(tcp, "dstport", 0))
        window_size = safe_int(getattr(tcp, "window_size", 0))

        # ======================
        # FLAGS
        # ======================
        flags = safe_int(getattr(tcp, "flags", 0))
        syn_flag = 1 if "S" in getattr(tcp, "flags", "") else 0
        ack_flag = 1 if "A" in getattr(tcp, "flags", "") else 0
        fin_flag = 1 if "F" in getattr(tcp, "flags", "") else 0
        rst_flag = 1 if "R" in getattr(tcp, "flags", "") else 0

        # ======================
        # IP FEATURES
        # ======================
        ip_len = safe_int(getattr(ip, "len", 0))
        ttl = safe_int(getattr(ip, "ttl", 0))
        proto = safe_int(getattr(ip, "proto", 0))

        # ======================
        # TIME FEATURES
        # ======================
        timestamp = float(pkt.sniff_timestamp)
        last_time = prev_state.get("last_time")

        iat = 0.0 if last_time is None else timestamp - last_time

        # ======================
        # SEQ/ACK DELTAS
        # ======================
        seq_delta = seq - prev_state.get("last_seq", seq)
        ack_delta = ack - prev_state.get("last_ack", ack)

        # ======================
        # UPDATE STATE
        # ======================
        prev_state["last_time"] = timestamp
        prev_state["last_seq"] = seq
        prev_state["last_ack"] = ack

        # ======================
        # LOSS FEATURES
        # ======================
        loss_flag = 1 if hasattr(tcp, "analysis_retransmission") else 0

        prev_state["loss_window"].append(loss_flag)

        if len(prev_state["loss_window"]) > 10:
            prev_state["loss_window"].pop(0)

        rolling_loss_rate = (
            sum(prev_state["loss_window"]) / len(prev_state["loss_window"])
            if prev_state["loss_window"]
            else 0.0
        )

        # ======================
        # FINAL 19 FEATURES
        # ======================
        return {
            "src_port": src_port,
            "dst_port": dst_port,
            "seq": seq,
            "ack": ack,
            "tcp_len": tcp_len,
            "window_size": window_size,
            "flags": flags,
            "syn_flag": syn_flag,
            "ack_flag": ack_flag,
            "fin_flag": fin_flag,
            "rst_flag": rst_flag,
            "ip_len": ip_len,
            "ttl": ttl,
            "proto": proto,
            "inter_arrival_time": iat,
            "seq_delta": seq_delta,
            "ack_delta": ack_delta,
            "rolling_loss_rate": rolling_loss_rate,
            "retransmission": loss_flag
        }

    except Exception as e:
        st.warning(f"Feature extraction error: {e}")
        return None
    
def run_stream():

    orchestrator = AgentOrchestrator()

    cap = pyshark.LiveCapture(
        interface=INTERFACE,
        display_filter="tcp"
    )

    prev_state = {
        "last_time": None,
        "last_seq": 0,
        "last_ack": 0,
        "loss_window": []
    }

    table_placeholder = st.empty()
    chart_placeholder = st.empty()
    metrics_placeholder = st.empty()

    for pkt in cap.sniff_continuously():

        if not st.session_state.running:
            break

        if st.session_state.packet_count >= MAX_PACKETS:
            st.warning("Reached max packet limit")
            break

        packet = extract_packet_features(pkt, prev_state)

        if packet is None:
            continue

        decision = orchestrator.run(packet)

        packet["decision"] = decision

        st.session_state.data.append(packet)
        st.session_state.packet_count += 1

        # Limit memory
        if len(st.session_state.data) > 200:
            st.session_state.data.pop(0)

        df = pd.DataFrame(st.session_state.data)


        with metrics_placeholder.container():
            col1, col2, col3 = st.columns(3)

            col1.metric("Total Packets", len(df))
            col2.metric("Avg Loss Rate", f"{df['rolling_loss_rate'].mean():.4f}")
            col3.metric("Retransmissions", int(df["retransmission"].sum()))

        with table_placeholder.container():
            st.subheader("📦 Live Packet Data")
            st.dataframe(df.tail(20), use_container_width=True)

        with chart_placeholder.container():
            st.subheader("📊 Rolling Loss Rate")
            st.line_chart(df["rolling_loss_rate"])

            st.subheader("🎯 Decision Distribution")
            st.bar_chart(df["decision"].value_counts())

        time.sleep(0.3)


if st.session_state.running:
    run_stream()
else:
    st.info("Click ▶️ Start Capture to begin")