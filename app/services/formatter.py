from typing import List, Dict


class OCRFormatter:
    """
    Cleans PaddleOCR detections and reconstructs readable text.
    """

    def __init__(
        self,
        confidence_threshold=0.40,
        min_box_height=8,
        line_gap_ratio=0.6,
    ):
        self.confidence_threshold = confidence_threshold
        self.min_box_height = min_box_height
        self.line_gap_ratio = line_gap_ratio

    def format(self, detections: List[Dict]) -> str:
        """
        detections = [
            {
                "text": "...",
                "score": 0.98,
                "x": ...,
                "y": ...,
                "height": ...
            }
        ]
        """

        # -------------------------
        # Step 1 – Filter detections
        # -------------------------
        filtered = []

        for d in detections:

            if d["score"] < self.confidence_threshold:
                continue

            if d["height"] < self.min_box_height:
                continue

            filtered.append(d)

        if not filtered:
            return ""

        # -------------------------
        # Step 2 – Reading order
        # -------------------------
        filtered.sort(key=lambda x: (x["y"], x["x"]))

        # -------------------------
        # Step 3 – Compute adaptive line gap
        # -------------------------
        heights = [d["height"] for d in filtered]
        median_height = sorted(heights)[len(heights) // 2]
        line_gap = max(median_height * self.line_gap_ratio, 10)

        # -------------------------
        # Step 4 – Merge lines
        # -------------------------
        lines = []
        current_line = []
        previous_y = None

        for item in filtered:

            if previous_y is None:
                current_line.append(item["text"])
                previous_y = item["y"]
                continue

            if abs(item["y"] - previous_y) <= line_gap:
                current_line.append(item["text"])
            else:
                lines.append(" ".join(current_line))
                current_line = [item["text"]]

            previous_y = item["y"]

        if current_line:
            lines.append(" ".join(current_line))

        return "\n".join(lines)


formatter = OCRFormatter()