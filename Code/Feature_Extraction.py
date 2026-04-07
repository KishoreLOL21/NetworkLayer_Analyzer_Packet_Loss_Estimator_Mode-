import pyshark
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import SelectKBest, f_classif
from tqdm import tqdm
import warnings
import asyncio
import nest_asyncio

warnings.filterwarnings("ignore")

asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
nest_asyncio.apply()

PCAP_FILES = [
    "capture_loss0.pcap",
    "capture_loss10.pcap",
    "capture_loss15.pcap",
    "capture_loss5.pcap",
    "capture_loss20.pcap"
]

OUTPUT_CSV = "features_selected.csv"
TOP_K = 10
PCA_COMPONENTS = 5


def parse_pcap(pcap_file):
    print(f"\n[*] Parsing {pcap_file} ...")
    cap = pyshark.FileCapture(pcap_file, display_filter="tcp")

    def to_int(val):
        try:
            return int(val)
        except:
            return 1 if str(val).strip().lower() == "true" else 0

    records = []

    for pkt in tqdm(cap, desc=f"Packets ({pcap_file})", unit="pkt"):
        try:
            tcp = pkt.tcp
            ip = pkt.ip

            record = {
                "ip_ttl": int(ip.ttl),
                "ip_len": int(ip.len),
                "ip_proto": int(ip.proto),

                "tcp_srcport": int(tcp.srcport),
                "tcp_dstport": int(tcp.dstport),
                "tcp_seq": int(tcp.seq),
                "tcp_ack": int(tcp.ack),
                "tcp_len": int(tcp.len),
                "tcp_window_size": int(tcp.window_size_value),
                "tcp_hdr_len": int(tcp.hdr_len),

                "flag_syn": to_int(tcp.flags_syn),
                "flag_ack": to_int(tcp.flags_ack),
                "flag_fin": to_int(tcp.flags_fin),
                "flag_rst": to_int(tcp.flags_reset),
                "flag_push": to_int(tcp.flags_push),
                "flag_urg": to_int(tcp.flags_urg),

                "frame_time_delta": float(pkt.frame_info.time_delta),
                "frame_time_epoch": float(pkt.frame_info.time_epoch),

                # Label
                "packet_loss": 1 if hasattr(tcp, "analysis_retransmission") else 0,
            }

            records.append(record)

        except AttributeError:
            continue

    cap.close()

    df = pd.DataFrame(records)

    if df.empty:
        print(f"[!] No TCP packets found in {pcap_file}")
        return df

    df["frame_time_epoch"] = df["frame_time_epoch"] - df["frame_time_epoch"].min()

    print(f"[+] {pcap_file}: {len(df)} packets | Loss: {df['packet_loss'].sum()}")

    return df


def parse_multiple_pcaps(pcap_files):
    all_dfs = []

    for i, file in enumerate(pcap_files):
        df = parse_pcap(file)

        if not df.empty:
            df["file_id"] = i
            df["source_file"] = file
            all_dfs.append(df)

    if not all_dfs:
        raise ValueError("❌ No valid data extracted from PCAP files.")

    combined_df = pd.concat(all_dfs, ignore_index=True)

    print("\n[+] COMBINED DATASET SUMMARY")
    print(f"Total packets : {len(combined_df)}")
    print(f"Columns       : {len(combined_df.columns)}")
    print(f"Loss distribution:\n{combined_df['packet_loss'].value_counts()}")

    return combined_df


def engineer_features(df):
    df = df.sort_values(["file_id", "frame_time_epoch"]).reset_index(drop=True)

    steps = [
        ("Inter-arrival time", lambda d: d.groupby("file_id")["frame_time_epoch"].diff().fillna(0)),
        ("Sequence delta", lambda d: d.groupby("file_id")["tcp_seq"].diff().fillna(0)),
        ("ACK delta", lambda d: d.groupby("file_id")["tcp_ack"].diff().fillna(0)),
        ("Rolling mean len", lambda d: d.groupby("file_id")["tcp_len"].rolling(5, min_periods=1).mean().reset_index(level=0, drop=True)),
        ("Rolling std len", lambda d: d.groupby("file_id")["tcp_len"].rolling(5, min_periods=1).std().fillna(0).reset_index(level=0, drop=True)),
        ("Rolling loss rate", lambda d: d.groupby("file_id")["packet_loss"].rolling(10, min_periods=1).mean().reset_index(level=0, drop=True)),
    ]

    col_names = ["iat", "seq_delta", "ack_delta",
                 "rolling_mean_len", "rolling_std_len", "rolling_loss_rate"]

    for (desc, fn), col in tqdm(zip(steps, col_names), total=len(steps),
                               desc="Engineering features", unit="feature"):
        df[col] = fn(df)

    return df


def select_features(df, top_k=TOP_K, n_pca=PCA_COMPONENTS):
    label_col = "packet_loss"
    drop_cols = [label_col, "frame_time_epoch", "source_file", "file_id"]

    X = df.drop(columns=drop_cols, errors="ignore").fillna(0)
    y = df[label_col]

    feature_names = X.columns.tolist()

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # SelectKBest
    selector = SelectKBest(score_func=f_classif, k=min(top_k, len(feature_names)))
    selector.fit(X_scaled, y)
    kbest_scores = pd.Series(selector.scores_, index=feature_names).sort_values(ascending=False)
    kbest_features = set(kbest_scores.head(top_k).index.tolist())

    # Random Forest
    rf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    rf.fit(X_scaled, y)
    rf_scores = pd.Series(rf.feature_importances_, index=feature_names).sort_values(ascending=False)
    rf_features = set(rf_scores.head(top_k).index.tolist())

    # PCA
    pca = PCA(n_components=min(n_pca, X_scaled.shape[1]))
    pca.fit(X_scaled)
    explained = pca.explained_variance_ratio_

    loadings = pd.DataFrame(
        pca.components_.T,
        index=feature_names,
        columns=[f"PC{i+1}" for i in range(pca.n_components_)]
    )
    pca_features = set(loadings.abs().max(axis=1).sort_values(ascending=False).head(top_k).index.tolist())

    intersection = kbest_features | rf_features | pca_features
    ordered_intersection = [f for f in feature_names if f in intersection]

    print("\n[+] Feature Selection Results")
    print(f"  KBest ({len(kbest_features)}) : {sorted(kbest_features)}")
    print(f"  RF    ({len(rf_features)}) : {sorted(rf_features)}")
    print(f"  PCA   ({len(pca_features)}) : {sorted(pca_features)}")
    print(f"\n✅ Intersection ({len(intersection)}) : {sorted(intersection)}")
    print("Explained variance:", np.round(explained, 3), "Total:", explained.sum())

    if len(intersection) == 0:
        raise ValueError("❌ Intersection is empty! Try increasing TOP_K.")

    return {
        "kbest_features":    sorted(kbest_features),
        "rf_features":       sorted(rf_features),
        "pca_features":      sorted(pca_features),
        "selected_features": ordered_intersection,
        "feature_names":     feature_names,
        "scaler":            scaler,
    }


def export_csv(df, results, output_path=OUTPUT_CSV):
    selected = results["selected_features"]

    selected = [c for c in selected if c in df.columns]

    print(f"\n[*] Exporting {len(selected)} features...")

    out_df = df[selected].copy()
    out_df["packet_loss"] = df["packet_loss"].values

    out_df.to_csv(output_path, index=False)

    print(f"[+] Saved dataset → {output_path}")


if __name__ == "__main__":
    df = parse_multiple_pcaps(PCAP_FILES)

    df = engineer_features(df)

    results = select_features(df)

    export_csv(df, results)

    print("\n✅ DONE! Multi-PCAP dataset ready for training.")
