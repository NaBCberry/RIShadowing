import difflib
import re
from typing import List, Dict, Tuple


class ShadowComparator:
    def __init__(self, reference_text: str):
        self._ref_text = reference_text.strip()
        self._ref_words = self._tokenize(self._ref_text)
        self._word_mask = [bool(re.match(r"[a-zA-Z']", w)) for w in self._ref_words]
        self._word_timings = []

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        words = re.findall(r"[a-zA-Z']+|\S", text.lower())
        return words

    def set_estimated_timings(self, audio_duration: float):
        if not self._ref_words:
            return
        words_per_sec = len(self._ref_words) / max(audio_duration, 0.1)
        self._word_timings = []
        for i, word in enumerate(self._ref_words):
            start = i / words_per_sec
            end = (i + 1) / words_per_sec
            self._word_timings.append({
                "word": word,
                "start": start,
                "end": end,
                "ref_index": i,
            })

    def set_word_timings(self, asr_words: list):
        if not asr_words or not self._ref_words:
            return

        asr_word_texts = [w.get("word", "").lower() for w in asr_words]
        sm = difflib.SequenceMatcher(
            None, [w.lower() for w in self._ref_words], asr_word_texts
        )
        alignment = sm.get_opcodes()

        self._word_timings = []
        for tag, i1, i2, j1, j2 in alignment:
            if tag == "equal":
                for k in range(i2 - i1):
                    ref_idx = i1 + k
                    asr_idx = j1 + k
                    self._word_timings.append({
                        "word": self._ref_words[ref_idx],
                        "start": asr_words[asr_idx].get("start", 0.0),
                        "end": asr_words[asr_idx].get("end", 0.0),
                        "ref_index": ref_idx,
                    })
            elif tag == "replace":
                for k in range(min(i2 - i1, j2 - j1)):
                    ref_idx = i1 + k
                    asr_idx = j1 + k
                    self._word_timings.append({
                        "word": self._ref_words[ref_idx],
                        "start": asr_words[asr_idx].get("start", 0.0),
                        "end": asr_words[asr_idx].get("end", 0.0),
                        "ref_index": ref_idx,
                    })
                for k in range(min(i2 - i1, j2 - j1), i2 - i1):
                    ref_idx = i1 + k
                    self._word_timings.append({
                        "word": self._ref_words[ref_idx],
                        "start": 0.0, "end": 0.0,
                        "ref_index": ref_idx,
                    })
            elif tag == "delete":
                for k in range(i1, i2):
                    self._word_timings.append({
                        "word": self._ref_words[k],
                        "start": 0.0, "end": 0.0,
                        "ref_index": k,
                    })

        if not self._word_timings:
            return

        for i in range(len(self._word_timings)):
            if self._word_timings[i]["end"] <= 0:
                if i > 0 and self._word_timings[i - 1]["end"] > 0:
                    prev_end = self._word_timings[i - 1]["end"]
                    next_start = prev_end + 999
                    for j in range(i, len(self._word_timings)):
                        if self._word_timings[j]["end"] > 0:
                            next_start = self._word_timings[j]["start"]
                            break
                    gap = next_start - prev_end
                    n_missing = sum(
                        1 for j in range(i, len(self._word_timings))
                        if self._word_timings[j]["end"] <= 0 and self._word_timings[j]["start"] < prev_end + 1
                    )
                    n_missing = max(n_missing, 1)
                    slot = gap / n_missing
                    missing_idx = 0
                    for j in range(i, len(self._word_timings)):
                        if self._word_timings[j]["end"] <= 0:
                            t = prev_end + missing_idx * slot
                            self._word_timings[j]["start"] = t
                            self._word_timings[j]["end"] = t + slot
                            missing_idx += 1
                            if self._word_timings[j]["start"] >= next_start - 0.01:
                                break
                    break

        print(f"[Comparator] aligned {len(self._word_timings)} words via SequenceMatcher")

    @property
    def reference_words(self) -> List[str]:
        return list(self._ref_words)

    @property
    def word_count(self) -> int:
        return len(self._ref_words)

    def get_current_ref_word_index(self, ref_elapsed: float) -> int:
        if not self._word_timings:
            return 0
        for i, t in enumerate(self._word_timings):
            if ref_elapsed < t["end"]:
                return i
        return len(self._word_timings)

    def compare_speed(
        self, recognized_words: List[dict], ref_elapsed: float
    ) -> Dict:
        current_ref_idx = self.get_current_ref_word_index(ref_elapsed)

        if not recognized_words:
            return {
                "status": "waiting",
                "message": "等待语音...",
                "color": "gray",
                "ref_index": current_ref_idx,
                "user_index": 0,
                "gap": 0,
            }

        user_word_count = len(recognized_words)

        gap = user_word_count - current_ref_idx

        if abs(gap) <= 1:
            status = "good"
            message = "速度合适 ✓"
            color = "green"
        elif abs(gap) <= 2:
            if gap > 0:
                status = "fast"
                message = f"稍快 — 领先 {gap} 个词 ↑"
            else:
                status = "slow"
                message = f"稍慢 — 落后 {abs(gap)} 个词 ↓"
            color = "yellow"
        elif gap > 2:
            status = "fast"
            message = f"太快了! 领先 {gap} 个词 ↑↑"
            color = "red"
        else:
            status = "slow"
            message = f"太慢了! 落后 {abs(gap)} 个词 ↓↓"
            color = "red"

        return {
            "status": status,
            "message": message,
            "color": color,
            "ref_index": current_ref_idx,
            "user_index": user_word_count,
            "gap": gap,
        }

    def compare_accuracy(
        self, recognized_words: List[dict], ref_elapsed: float
    ) -> Dict:
        current_ref_idx = self.get_current_ref_word_index(ref_elapsed)

        if current_ref_idx == 0:
            return {
                "status": "waiting",
                "message": "等待开始...",
                "color": "gray",
                "score": 0.0,
                "breakdown": [],
            }

        ref_slice = self._ref_words[:current_ref_idx]

        user_text = " ".join(w["word"] for w in recognized_words)
        user_words_all = self._tokenize(user_text) if user_text.strip() else []

        user_words_filtered = [
            w for w in user_words_all if re.match(r"[a-zA-Z']", w)
        ]
        ref_words_filtered = [
            (i, w) for i, w in enumerate(ref_slice) if self._word_mask[i]
        ]

        breakdown = []
        green_count = 0
        yellow_count = 0
        red_count = 0

        for j, (ref_i, ref_word) in enumerate(ref_words_filtered):
            if j < len(user_words_filtered):
                user_word = user_words_filtered[j]
                ratio = difflib.SequenceMatcher(None, ref_word, user_word).ratio()
                if ratio >= 0.8:
                    color = "green"
                    green_count += 1
                elif ratio >= 0.5:
                    color = "yellow"
                    yellow_count += 1
                else:
                    color = "red"
                    red_count += 1
            else:
                ratio = 0.0
                color = "red"
                red_count += 1
                user_word = ""

            breakdown.append({
                "ref_word": ref_word,
                "user_word": user_word,
                "ratio": ratio,
                "color": color,
                "ref_index": ref_i,
            })

        total = len(ref_words_filtered)
        if total == 0:
            score = 0.0
            overall_color = "gray"
            overall_status = "waiting"
        else:
            score = green_count / total
            if score >= 0.8:
                overall_color = "green"
                overall_status = "good"
            elif score >= 0.5:
                overall_color = "yellow"
                overall_status = "fair"
            else:
                overall_color = "red"
                overall_status = "poor"

        status_messages = {
            "good": f"准确度优秀 ({green_count}/{total})",
            "fair": f"准确度一般 ({green_count}/{total})",
            "poor": f"准确度较低 ({green_count}/{total})",
            "waiting": "等待开始...",
        }

        return {
            "status": overall_status,
            "message": status_messages.get(overall_status, ""),
            "color": overall_color,
            "score": score,
            "green_count": green_count,
            "yellow_count": yellow_count,
            "red_count": red_count,
            "ref_index": current_ref_idx,
            "breakdown": breakdown,
        }

    def get_reference_words_for_display(
        self, ref_elapsed: float
    ) -> List[Tuple[str, str, int]]:
        current_idx = self.get_current_ref_word_index(ref_elapsed)
        result = []
        for i, word in enumerate(self._ref_words):
            if i < current_idx:
                status = "past"
            elif i == current_idx:
                status = "current"
            else:
                status = "future"
            result.append((word, status, i))
        return result
