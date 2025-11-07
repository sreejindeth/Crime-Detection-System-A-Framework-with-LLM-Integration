import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

import cv2
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    classification_report,
    confusion_matrix,
    precision_recall_curve,
    roc_auc_score,
    roc_curve,
)

from detection import AccidentDetectionModel

CLASS_LABELS = {
    "Accident": 0,
    "Non Accident": 1,
}
CLASS_NAMES = ["Accident", "Non Accident"]
IMG_SIZE = (250, 250)


def load_dataset(split_dir: Path) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    images: List[np.ndarray] = []
    labels: List[int] = []
    paths: List[str] = []

    if not split_dir.exists():
        raise FileNotFoundError(f"Dataset split not found: {split_dir}")

    for class_name, label_idx in CLASS_LABELS.items():
        class_dir = split_dir / class_name
        if not class_dir.exists():
            raise FileNotFoundError(f"Expected class directory missing: {class_dir}")

        for image_path in sorted(class_dir.glob("*")):
            if image_path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".bmp"}:
                continue
            image = cv2.imread(str(image_path))
            if image is None:
                print(f"Warning: Unable to read image {image_path}, skipping.")
                continue
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            image = cv2.resize(image, IMG_SIZE)
            images.append(image.astype(np.float32))
            labels.append(label_idx)
            paths.append(str(image_path))

    if not images:
        raise RuntimeError(f"No images were loaded from {split_dir}")

    X = np.stack(images, axis=0)
    y = np.array(labels, dtype=np.int32)
    return X, y, paths


def ensure_results_dir(base: Path) -> Tuple[Path, Path]:
    base.mkdir(parents=True, exist_ok=True)
    images_dir = base / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    return base, images_dir


def plot_confusion_matrix(cm: np.ndarray, output_path: Path) -> None:
    plt.figure(figsize=(6, 5))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=CLASS_NAMES,
        yticklabels=CLASS_NAMES,
    )
    plt.xlabel("Predicted")
    plt.ylabel("Actual")
    plt.title("Confusion Matrix")
    plt.tight_layout()
    plt.savefig(output_path, dpi=250)
    plt.close()


def plot_roc_curve(y_true: np.ndarray, scores: np.ndarray, output_path: Path) -> float:
    fpr, tpr, _ = roc_curve(y_true, scores, pos_label=0)
    roc_auc = roc_auc_score(y_true == 0, scores)  # Convert to binary: Accident (0) = True
    plt.figure(figsize=(6, 5))
    plt.plot(fpr, tpr, color="darkorange", lw=2, label=f"ROC curve (AUC = {roc_auc:.3f})")
    plt.plot([0, 1], [0, 1], color="navy", lw=1, linestyle="--")
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("Receiver Operating Characteristic")
    plt.legend(loc="lower right")
    plt.tight_layout()
    plt.savefig(output_path, dpi=250)
    plt.close()
    return roc_auc


def plot_precision_recall_curve(y_true: np.ndarray, scores: np.ndarray, output_path: Path) -> float:
    precision, recall, _ = precision_recall_curve(y_true == 0, scores, pos_label=1)
    pr_auc = average_precision_score(y_true == 0, scores)  # Use this instead of np.trapz()
    plt.figure(figsize=(6, 5))
    plt.plot(recall, precision, color="green", lw=2, label=f"PR curve (AUC ≈ {pr_auc:.3f})")
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.title("Precision-Recall Curve")
    plt.legend(loc="lower left")
    plt.tight_layout()
    plt.savefig(output_path, dpi=250)
    plt.close()
    return pr_auc


def evaluate(split: str, data_root: Path, results_dir: Path) -> None:
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    results_dir, images_dir = ensure_results_dir(results_dir)

    split_dir = data_root / split
    print(f"Loading dataset from {split_dir}...")
    X, y_true, paths = load_dataset(split_dir)
    print(f"Loaded {len(X)} images for split '{split}'.")

    print("Loading trained model...")
    model = AccidentDetectionModel("model.json", "model_weights.keras")
    probs = model.loaded_model.predict(X, batch_size=32, verbose=1)
    y_pred = np.argmax(probs, axis=1)

    accident_scores = probs[:, CLASS_LABELS["Accident"]]

    accuracy = accuracy_score(y_true, y_pred)
    report = classification_report(y_true, y_pred, target_names=CLASS_NAMES, output_dict=True)
    cm = confusion_matrix(y_true, y_pred)

    cm_path = images_dir / f"confusion_matrix_{split}_{timestamp}.png"
    roc_path = images_dir / f"roc_curve_{split}_{timestamp}.png"
    pr_path = images_dir / f"precision_recall_{split}_{timestamp}.png"

    plot_confusion_matrix(cm, cm_path)
    roc_auc = plot_roc_curve(y_true, accident_scores, roc_path)
    pr_auc = plot_precision_recall_curve(y_true, accident_scores, pr_path)

    metrics = {
        "split": split,
        "timestamp": timestamp,
        "num_samples": int(len(X)),
        "accuracy": float(accuracy),
        "roc_auc": float(roc_auc),
        "pr_auc": float(pr_auc),
        "classification_report": report,
        "confusion_matrix": cm.tolist(),
        "image_outputs": {
            "confusion_matrix": str(cm_path.relative_to(results_dir.parent)),
            "roc_curve": str(roc_path.relative_to(results_dir.parent)),
            "precision_recall_curve": str(pr_path.relative_to(results_dir.parent)),
        },
    }

    metrics_path = results_dir / f"metrics_{split}_{timestamp}.json"
    with open(metrics_path, "w", encoding="utf-8") as fp:
        json.dump(metrics, fp, indent=2)

    text_report_path = results_dir / f"classification_report_{split}_{timestamp}.txt"
    with open(text_report_path, "w", encoding="utf-8") as fp:
        fp.write(classification_report(y_true, y_pred, target_names=CLASS_NAMES))

    print("Evaluation complete. Summary:")
    print(f"  Accuracy: {accuracy:.4f}")
    print(f"  ROC AUC : {roc_auc:.4f}")
    print(f"  PR  AUC : {pr_auc:.4f}")
    print(f"  Confusion matrix saved to: {cm_path}")
    print(f"  ROC curve saved to:        {roc_path}")
    print(f"  Precision-Recall saved to: {pr_path}")
    print(f"  Metrics JSON saved to:     {metrics_path}")
    print(f"  Classification report:     {text_report_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate accident detection model on dataset splits.")
    parser.add_argument(
        "--split",
        default="test",
        choices=["train", "val", "test"],
        help="Dataset split to evaluate (default: test)",
    )
    parser.add_argument(
        "--data-root",
        default="data",
        help="Root directory containing split folders (train/val/test)",
    )
    parser.add_argument(
        "--output-dir",
        default="performance_results",
        help="Directory to store evaluation metrics and plots",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data_root = Path(args.data_root).resolve()
    results_dir = Path(args.output_dir).resolve()
    evaluate(args.split, data_root, results_dir)


if __name__ == "__main__":
    main()
