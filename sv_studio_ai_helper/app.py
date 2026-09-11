"""MP3에 어울리는, 사용자가 보유한 Synthesizer V 보이스를 추천하는 앱."""

from __future__ import annotations

import os
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk

from gemini_recommender import (
    AQ_KEY_PREFIX,
    MAX_INLINE_AUDIO_BYTES,
    GeminiPronunciationConverter,
    GeminiRecommender,
    RecommendationError,
)
from voices_data import voices


HANGUL_BASE = 0xAC00
HANGUL_END = 0xD7A3
INITIAL_COUNT = 19
VOWEL_COUNT = 21
FINAL_COUNT = 28
SYLLABLE_BLOCK = VOWEL_COUNT * FINAL_COUNT

INITIAL_ROMANIZATION = [
    "g",
    "kk",
    "n",
    "d",
    "tt",
    "r",
    "m",
    "b",
    "pp",
    "s",
    "ss",
    "",
    "j",
    "jj",
    "ch",
    "k",
    "t",
    "p",
    "h",
]

VOWEL_ROMANIZATION = [
    "a",
    "ae",
    "ya",
    "yae",
    "eo",
    "e",
    "yeo",
    "ye",
    "o",
    "wa",
    "wae",
    "oe",
    "yo",
    "u",
    "wo",
    "we",
    "wi",
    "yu",
    "eu",
    "ui",
    "i",
]

FINAL_ROMANIZATION_BEFORE_VOWEL = [
    "",
    "g",
    "kk",
    "gs",
    "n",
    "nj",
    "nh",
    "d",
    "r",
    "rg",
    "rm",
    "rb",
    "rs",
    "rt",
    "rp",
    "rh",
    "m",
    "b",
    "bs",
    "t",
    "t",
    "ng",
    "t",
    "t",
    "k",
    "t",
    "p",
    "h",
]

FINAL_ROMANIZATION_CLOSED = [
    "",
    "k",
    "k",
    "k",
    "n",
    "n",
    "n",
    "t",
    "l",
    "k",
    "m",
    "l",
    "l",
    "l",
    "p",
    "l",
    "m",
    "p",
    "p",
    "t",
    "t",
    "ng",
    "t",
    "t",
    "k",
    "t",
    "p",
    "t",
]


def romanize_korean_text(text: str) -> str:
    """한글 문장을 Lexilogos식에 가까운 기본 라틴 문자 발음으로 바꾼다."""
    result: list[str] = []

    for index, char in enumerate(text):
        if not _is_hangul_syllable(char):
            result.append(char)
            continue

        initial_index, vowel_index, final_index = _decompose_hangul(char)
        next_initial_index = _next_hangul_initial_index(text, index)
        final_table = (
            FINAL_ROMANIZATION_BEFORE_VOWEL
            if next_initial_index == 11
            else FINAL_ROMANIZATION_CLOSED
        )

        result.append(
            INITIAL_ROMANIZATION[initial_index]
            + VOWEL_ROMANIZATION[vowel_index]
            + final_table[final_index]
        )

    return "".join(result)


def _is_hangul_syllable(char: str) -> bool:
    code = ord(char)
    return HANGUL_BASE <= code <= HANGUL_END


def _decompose_hangul(char: str) -> tuple[int, int, int]:
    syllable_index = ord(char) - HANGUL_BASE
    initial_index = syllable_index // SYLLABLE_BLOCK
    vowel_index = (syllable_index % SYLLABLE_BLOCK) // FINAL_COUNT
    final_index = syllable_index % FINAL_COUNT
    return initial_index, vowel_index, final_index


def _next_hangul_initial_index(text: str, index: int) -> int | None:
    next_index = index + 1
    if next_index >= len(text) or not _is_hangul_syllable(text[next_index]):
        return None
    return _decompose_hangul(text[next_index])[0]


class VoiceRecommenderApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Synthesizer V Gemini helper")
        self.geometry("840x820")
        self.minsize(680, 580)

        self.selected_path = tk.StringVar()
        self.status = tk.StringVar(value="보유한 보이스를 선택해 주세요.")
        self.selection_summary = tk.StringVar()
        self.pronunciation_input = tk.StringVar()
        self.pronunciation_status = tk.StringVar(
            value="영어 단어나 짧은 구절을 입력해 주세요."
        )
        self.latest_phonemes = ""
        self.korean_input = tk.StringVar()
        self.korean_status = tk.StringVar(value="한국어를 입력해 주세요.")
        self.latest_korean_romanization = ""
        self.voice_variables = {name: tk.BooleanVar(value=False) for name in voices}
        self.uses_aq_inline_audio = self._uses_aq_inline_audio_key()
        self._build_ui()
        self._update_selection_summary()

    @staticmethod
    def _uses_aq_inline_audio_key() -> bool:
        api_key = (os.getenv("GEMINI_API_KEY") or "").strip()
        return api_key.startswith(AQ_KEY_PREFIX)

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)

        notebook = ttk.Notebook(root)
        notebook.pack(fill="both", expand=True)

        recommender_tab = ttk.Frame(notebook, padding=12)
        pronunciation_tab = ttk.Frame(notebook, padding=12)
        korean_tab = ttk.Frame(notebook, padding=12)
        notebook.add(recommender_tab, text="Synthesizer V 보이스를 추천")
        notebook.add(pronunciation_tab, text="영어 입력 하면 신스븨 발음 출력")
        notebook.add(korean_tab, text="한국어 입력하면 영어 발음 출력")

        self._build_recommender_tab(recommender_tab)
        self._build_pronunciation_tab(pronunciation_tab)
        self._build_korean_romanization_tab(korean_tab)

    def _build_recommender_tab(self, container: ttk.Frame) -> None:
        container.columnconfigure(0, weight=1)
        container.rowconfigure(6, weight=1)

        ttk.Label(
            container,
            text="mp3 Synthesizer V voice matcher",
            font=("Malgun Gothic", 16, "bold"),
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            container,
            text="보유한 보이스만 선택하면, Gemini가 mp3에 맞는 보이스를 추천합니다.",
        ).grid(row=1, column=0, sticky="w", pady=(5, 8))

        if self.uses_aq_inline_audio:
            max_mebibytes = MAX_INLINE_AUDIO_BYTES // (1024 * 1024)
            connection_text = (
                f"AQ. 키 감지: Gemini API로 MP3를 직접 전송하며 "
                f"{max_mebibytes}MB 이하여야 합니다."
            )
        else:
            connection_text = "일반 Gemini API 키 감지: MP3를 Gemini Files API로 전송합니다."
        ttk.Label(container, text=connection_text, foreground="#356a3c").grid(
            row=2, column=0, sticky="w", pady=(0, 10)
        )

        self._build_voice_selector(container).grid(row=3, column=0, sticky="nsew")

        file_frame = ttk.Frame(container)
        file_frame.grid(row=4, column=0, sticky="ew", pady=(14, 0))
        file_frame.columnconfigure(0, weight=1)
        ttk.Entry(file_frame, textvariable=self.selected_path, state="readonly").grid(
            row=0, column=0, sticky="ew", padx=(0, 8)
        )
        ttk.Button(file_frame, text="MP3 파일 선택", command=self._choose_file).grid(
            row=0, column=1
        )

        action_frame = ttk.Frame(container)
        action_frame.grid(row=5, column=0, sticky="ew", pady=12)
        self.recommend_button = ttk.Button(
            action_frame,
            text="선택한 보이스 중 추천 받기",
            command=self._start_recommendation,
        )
        self.recommend_button.pack(side="left")
        self.progress = ttk.Progressbar(action_frame, mode="indeterminate", length=150)
        self.progress.pack(side="left", padx=12)
        ttk.Label(action_frame, textvariable=self.status).pack(side="left")

        self.result = scrolledtext.ScrolledText(
            container,
            wrap="word",
            font=("Malgun Gothic", 10),
            state="disabled",
            padx=10,
            pady=10,
        )
        self.result.grid(row=6, column=0, sticky="nsew")
        self._set_result(
            "사용 순서\n\n"
            "1. 위 목록에서 실제로 보유한 보이스를 모두 체크합니다.\n"
            "2. 분석할 MP3 파일을 고릅니다.\n"
            "3. 추천 버튼을 누르면 선택한 보이스 중 하나만 결과로 나옵니다.\n\n"

            "Gemini가 음악을 분석하지 못했습니다. API 키, 선택한 모델명,인터넷 연결을 확인한 뒤 다시 시도하세요. 세부 오류: 503 이 출력되는 경우에는 gemini 서버가 붐비는 ( 503 이 붐비는 것입니다. ) 것이니 이 창을 닫으시고 5-10 분 정도 후에 다시 시도하여 주시기 바랍니다."

        )

    def _build_pronunciation_tab(self, container: ttk.Frame) -> None:
        container.columnconfigure(0, weight=1)
        container.rowconfigure(4, weight=1)

        ttk.Label(
            container,
            text="영어 단어 → Synthesizer V 노트 발음",
            font=("Malgun Gothic", 16, "bold"),
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            container,
            text=(
                "영어 단어 또는 짧은 구절을 입력하면 Gemini가 Synthesizer V의 "
                "영어 phoneme 칸에 붙여넣기 좋은 발음을 만들어 줍니다."
            ),
            wraplength=760,
        ).grid(row=1, column=0, sticky="w", pady=(5, 12))

        input_frame = ttk.Frame(container)
        input_frame.grid(row=2, column=0, sticky="ew")
        input_frame.columnconfigure(0, weight=1)
        ttk.Entry(input_frame, textvariable=self.pronunciation_input).grid(
            row=0, column=0, sticky="ew", padx=(0, 8)
        )
        self.pronunciation_button = ttk.Button(
            input_frame,
            text="발음 변환",
            command=self._start_pronunciation_conversion,
        )
        self.pronunciation_button.grid(row=0, column=1)
        ttk.Button(
            input_frame,
            text="결과 복사",
            command=self._copy_latest_phonemes,
        ).grid(row=0, column=2, padx=(8, 0))

        action_frame = ttk.Frame(container)
        action_frame.grid(row=3, column=0, sticky="ew", pady=12)
        self.pronunciation_progress = ttk.Progressbar(
            action_frame,
            mode="indeterminate",
            length=150,
        )
        self.pronunciation_progress.pack(side="left")
        ttk.Label(action_frame, textvariable=self.pronunciation_status).pack(
            side="left", padx=12
        )

        self.pronunciation_result = scrolledtext.ScrolledText(
            container,
            wrap="word",
            font=("Malgun Gothic", 11),
            state="disabled",
            padx=10,
            pady=10,
        )
        self.pronunciation_result.grid(row=4, column=0, sticky="nsew")
        self._set_pronunciation_result(
            "사용 순서\n\n"
            "1. 예: hello, world, beautiful, I'm alive 같은 영어 단어나 짧은 구절을 입력합니다.\n"
            "2. 발음 변환 버튼을 누릅니다.\n\n"
            "주의: Synthesizer V 보이스·언어 설정·노트 분할에 따라 약간의 수정이 필요할 수 있습니다."
        )

    def _build_korean_romanization_tab(self, container: ttk.Frame) -> None:
        container.columnconfigure(0, weight=1)
        container.rowconfigure(4, weight=1)

        ttk.Label(
            container,
            text="한국어 입력 → 영어식 발음 출력",
            font=("Malgun Gothic", 16, "bold"),
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            container,
            text=(
                "한국어 단어 또는 문장을 입력하면 앱 안에서 바로 "
                "영문 발음으로 바꿉니다."
            ),
            wraplength=760,
        ).grid(row=1, column=0, sticky="w", pady=(5, 12))

        input_frame = ttk.Frame(container)
        input_frame.grid(row=2, column=0, sticky="ew")
        input_frame.columnconfigure(0, weight=1)
        ttk.Entry(input_frame, textvariable=self.korean_input).grid(
            row=0, column=0, sticky="ew", padx=(0, 8)
        )
        ttk.Button(
            input_frame,
            text="영어 발음 출력",
            command=self._convert_korean_romanization,
        ).grid(row=0, column=1)
        ttk.Button(
            input_frame,
            text="결과 복사",
            command=self._copy_latest_korean_romanization,
        ).grid(row=0, column=2, padx=(8, 0))

        ttk.Label(container, textvariable=self.korean_status).grid(
            row=3, column=0, sticky="w", pady=12
        )

        self.korean_result = scrolledtext.ScrolledText(
            container,
            wrap="word",
            font=("Malgun Gothic", 11),
            state="disabled",
            padx=10,
            pady=10,
        )
        self.korean_result.grid(row=4, column=0, sticky="nsew")
        self._set_korean_result(
            "사용 순서\n\n"
            "1. 예: 안녕하세요, 한국어, 신스븨 같은 한국어를 입력합니다.\n"
            "2. 영어 발음 출력 버튼을 누릅니다.\n\n"
            "예시\n"
            "- 한국어 → hangugeo\n"
            "- 백마 → baekma\n"
            "- 같이 → gati\n\n"
        )

    def _build_voice_selector(self, parent: ttk.Frame) -> ttk.LabelFrame:
        selector = ttk.LabelFrame(parent, text="보유한 보이스 선택", padding=8)

        header = ttk.Frame(selector)
        header.pack(fill="x", pady=(0, 7))
        ttk.Label(header, textvariable=self.selection_summary).pack(side="left")
        ttk.Button(header, text="전체 선택", command=self._select_all).pack(side="right")
        ttk.Button(header, text="전체 해제", command=self._clear_all).pack(
            side="right", padx=(0, 6)
        )

        list_frame = ttk.Frame(selector)
        list_frame.pack(fill="both", expand=True)
        canvas = tk.Canvas(list_frame, height=210, highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        checkbox_frame = ttk.Frame(canvas)
        window_id = canvas.create_window((0, 0), window=checkbox_frame, anchor="nw")
        checkbox_frame.bind(
            "<Configure>",
            lambda _event: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.bind(
            "<Configure>",
            lambda event: canvas.itemconfigure(window_id, width=event.width),
        )
        canvas.bind(
            "<MouseWheel>",
            lambda event: canvas.yview_scroll(int(-event.delta / 120), "units"),
        )

        for index, (name, variable) in enumerate(self.voice_variables.items()):
            ttk.Checkbutton(
                checkbox_frame,
                text=name,
                variable=variable,
                command=self._update_selection_summary,
            ).grid(row=index // 2, column=index % 2, sticky="w", padx=(4, 24), pady=2)
        return selector

    def _select_all(self) -> None:
        for variable in self.voice_variables.values():
            variable.set(True)
        self._update_selection_summary()

    def _clear_all(self) -> None:
        for variable in self.voice_variables.values():
            variable.set(False)
        self._update_selection_summary()

    def _update_selection_summary(self) -> None:
        count = len(self._selected_voices())
        self.selection_summary.set(f"선택됨: {count} / {len(voices)}개")

    def _selected_voices(self) -> list[str]:
        return [name for name, variable in self.voice_variables.items() if variable.get()]

    def _choose_file(self) -> None:
        chosen = filedialog.askopenfilename(
            title="분석할 MP3 선택",
            filetypes=[("MP3 파일", "*.mp3"), ("모든 파일", "*.*")],
        )
        if not chosen:
            return

        if self.uses_aq_inline_audio:
            size = Path(chosen).stat().st_size
            if size > MAX_INLINE_AUDIO_BYTES:
                max_mebibytes = MAX_INLINE_AUDIO_BYTES // (1024 * 1024)
                messagebox.showwarning(
                    "MP3 파일이 너무 큼",
                    f"AQ. 키에서는 {max_mebibytes}MB 이하 MP3만 직접 전송할 수 있습니다.",
                )
                return

        self.selected_path.set(chosen)
        self.status.set(f"선택됨: {Path(chosen).name}")

    def _start_recommendation(self) -> None:
        owned_voices = self._selected_voices()
        if not owned_voices:
            messagebox.showwarning(
                "보유 보이스 선택 필요", "먼저 보유한 보이스를 한 개 이상 체크해 주세요."
            )
            return

        path = self.selected_path.get()
        if not path:
            messagebox.showwarning("MP3 파일 필요", "분석할 MP3 파일을 선택해 주세요.")
            return

        self.recommend_button.config(state="disabled")
        self.progress.start(12)
        self.status.set(f"Gemini가 선택한 {len(owned_voices)}개 보이스만 비교하는 중...")
        self._set_result("분석 중입니다. MP3 길이와 인터넷 상태에 따라 잠시 걸릴 수 있습니다.")
        threading.Thread(
            target=self._recommend_in_background,
            args=(path, owned_voices),
            daemon=True,
        ).start()

    def _recommend_in_background(self, path: str, owned_voices: list[str]) -> None:
        try:
            answer = GeminiRecommender(available_voices=owned_voices).recommend(path)
        except RecommendationError as error:
            self.after(0, self._show_error, str(error))
        except Exception as error:
            self.after(0, self._show_error, f"예상하지 못한 오류가 발생했습니다.\n{error}")
        else:
            self.after(0, self._show_recommendation, answer)

    def _start_pronunciation_conversion(self) -> None:
        english_text = self.pronunciation_input.get().strip()
        if not english_text:
            messagebox.showwarning(
                "영어 입력 필요",
                "변환할 영어 단어나 짧은 구절을 입력해 주세요.",
            )
            return

        self.latest_phonemes = ""
        self.pronunciation_button.config(state="disabled")
        self.pronunciation_progress.start(12)
        self.pronunciation_status.set("Gemini가 Synthesizer V용 발음으로 변환하는 중...")
        self._set_pronunciation_result("변환 중입니다. 잠시만 기다려 주세요.")
        threading.Thread(
            target=self._convert_pronunciation_in_background,
            args=(english_text,),
            daemon=True,
        ).start()

    def _convert_pronunciation_in_background(self, english_text: str) -> None:
        try:
            answer = GeminiPronunciationConverter().convert(english_text)
        except RecommendationError as error:
            self.after(0, self._show_pronunciation_error, str(error))
        except Exception as error:
            self.after(
                0,
                self._show_pronunciation_error,
                f"예상하지 못한 오류가 발생했습니다.\n{error}",
            )
        else:
            self.after(0, self._show_pronunciation_result, answer)

    def _show_pronunciation_result(self, answer: dict) -> None:
        self.latest_phonemes = answer["synthv_phonemes"]

        lines = [
            f"입력: {answer['input_text']}",
            "",
            "Synthesizer V에 넣을 발음",
            answer["synthv_phonemes"],
        ]
        if answer["syllable_hint"]:
            lines.extend(["", "노트 분할 힌트", answer["syllable_hint"]])
        if answer["notes"]:
            lines.extend(["", "설명", answer["notes"]])
        if answer["alternatives"]:
            lines.extend(["", "다른 발음 후보"])
            for item in answer["alternatives"]:
                lines.append(f"- {item['phonemes']}: {item['when_to_use']}")

        self._set_pronunciation_result("\n".join(lines))
        self._finish_pronunciation("발음 변환이 완료되었습니다.")

    def _show_pronunciation_error(self, error: str) -> None:
        self.latest_phonemes = ""
        self._set_pronunciation_result(f"변환하지 못했습니다.\n\n{error}")
        self._finish_pronunciation("오류가 발생했습니다.")
        messagebox.showerror("발음 변환 오류", error)

    def _finish_pronunciation(self, status: str) -> None:
        self.pronunciation_progress.stop()
        self.pronunciation_button.config(state="normal")
        self.pronunciation_status.set(status)

    def _copy_latest_phonemes(self) -> None:
        if not self.latest_phonemes:
            messagebox.showinfo("복사할 결과 없음", "먼저 발음을 변환해 주세요.")
            return

        self.clipboard_clear()
        self.clipboard_append(self.latest_phonemes)
        self.pronunciation_status.set("발음 결과를 클립보드에 복사했습니다.")

    def _convert_korean_romanization(self) -> None:
        korean_text = self.korean_input.get().strip()
        if not korean_text:
            messagebox.showwarning("한국어 입력 필요", "변환할 한국어를 입력해 주세요.")
            return

        romanized = romanize_korean_text(korean_text).strip()
        if not romanized:
            messagebox.showwarning("변환 결과 없음", "변환할 수 있는 한글이 없습니다.")
            return

        self.latest_korean_romanization = romanized
        self._set_korean_result(
            f"입력: {korean_text}\n\n"
            "영어식 발음\n"
            f"{romanized}\n\n"
            "참고\n"
            "이 기능은 Gemini를 쓰지 않는 기본 로마자 변환입니다. "
            "Synthesizer V에 영어 가사처럼 넣을 때의 발음 참고용으로 사용하고, "
            "실제 노래에서는 귀로 들으면서 조금 다듬는 것이 좋습니다."
        )
        self.korean_status.set("한국어 영문 발음 출력이 완료되었습니다.")

    def _copy_latest_korean_romanization(self) -> None:
        if not self.latest_korean_romanization:
            messagebox.showinfo("복사할 결과 없음", "먼저 한국어를 변환해 주세요.")
            return

        self.clipboard_clear()
        self.clipboard_append(self.latest_korean_romanization)
        self.korean_status.set("한국어 영문 발음 결과를 클립보드에 복사했습니다.")

    def _show_recommendation(self, answer: dict) -> None:
        lines = [
            f"가장 어울리는 보이스: {answer['recommended_voice']}",
            f"매칭 점수: {answer['match_score']} / 100",
            "",
            "추천 이유",
            answer["reason"],
        ]
        if answer["listening_notes"]:
            lines.extend(["", "들린 음악적 특징", answer["listening_notes"]])
        if answer["alternatives"]:
            lines.extend(["", "선택한 보이스 중 다른 후보"])
            for item in answer["alternatives"]:
                lines.append(f"- {item['voice']}: {item['reason']}")

        self._set_result("\n".join(lines))
        self._finish("추천이 완료되었습니다.")

    def _show_error(self, error: str) -> None:
        self._set_result(f"분석하지 못했습니다.\n\n{error}")
        self._finish("오류가 발생했습니다.")
        messagebox.showerror("추천 오류", error)

    def _finish(self, status: str) -> None:
        self.progress.stop()
        self.recommend_button.config(state="normal")
        self.status.set(status)

    def _set_result(self, text: str) -> None:
        self.result.config(state="normal")
        self.result.delete("1.0", tk.END)
        self.result.insert("1.0", text)
        self.result.config(state="disabled")

    def _set_pronunciation_result(self, text: str) -> None:
        self.pronunciation_result.config(state="normal")
        self.pronunciation_result.delete("1.0", tk.END)
        self.pronunciation_result.insert("1.0", text)
        self.pronunciation_result.config(state="disabled")

    def _set_korean_result(self, text: str) -> None:
        self.korean_result.config(state="normal")
        self.korean_result.delete("1.0", tk.END)
        self.korean_result.insert("1.0", text)
        self.korean_result.config(state="disabled")


if __name__ == "__main__":
    VoiceRecommenderApp().mainloop()
