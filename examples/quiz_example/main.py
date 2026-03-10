# Copyright (C) 2022 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR BSD-3-Clause

from QtBridge import bridge_instance, qtbridge, watch, effect, Change


class QuestionModel:
    """Q&A quiz model with auto-property tracking for navigation and scoring.
    """

    def __init__(self):
        # auto properties in QtBrides
        # automatic signal generation: current_indexChanged, scoreChanged
        # automatic property setter/getter generation
        # can be attached to @watch and @effect observers
        self.current_index = 0
        self.score = 0

        self._questions = [
            ["Why do programmers prefer dark mode?",
             "Because light attracts bugs."],
            ["Why do Java developers wear glasses?",
             "Because they can't C#."],
            ["Why did the programmer quit his job?",
             "He didn't get arrays."],
            ["How do programmers enjoy nature?",
             "They log out."],
            ["Why do programmers always mix up Halloween and Christmas?",
             "Because Oct 31 == Dec 25."],
            ["Why do programmers prefer iOS development?",
             "Because it's Swift."],
            ["Why was the function sad?",
             "It didn't return anything meaningful."],
            ["How many programmers does it take to change a light bulb?",
             "None — that's a hardware problem."],
            ["Why did the developer go broke?",
             "He used up all his cache."],
            ["What do you call 8 hobbits?", "A hobbyte."],
            ["Why did the programmer bring a ladder to work?",
             "To reach the high-level languages."],
            ["Why was the computer cold?",
             "Because it left it's windows open."],
            ["Why do astronauts use linux?",
             "Because they can't open windows in space."],
            ["How do developers stay in shape?",
             "They run endless loops."],
            ["Why was the API so lonely?",
             "No one wanted to make a call."],
            ["Why did the loop so tired?",
             "It had too many iterations."]
        ]

    @watch("current_index")
    def _on_question_changed(self, change: Change) -> None:
        """Logs whenever the user navigates to a different question."""
        total = len(self._questions)
        print(
            f"[watch] question navigated: "
            f"#{change.old + 1}/{total} → #{change.new + 1}/{total}"
        )

    @effect("score")
    def _on_score_updated(self) -> None:
        total = len(self._questions)
        suffix = " 🎉 Perfect score!" if self.score == total else ""
        print(f"[effect] score updated: {self.score}/{total}{suffix}")

    def next_question(self) -> None:
        self.current_index = (self.current_index + 1) % len(self._questions)

    def prev_question(self) -> None:
        self.current_index = (self.current_index - 1) % len(self._questions)

    def reveal_answer(self) -> None:
        self.score = self.score + 1

    def getItem(self, row: int, column: int) -> str:
        return self._questions[row][column]

    @property
    def items(self) -> dict[str]:
        return self._questions

    def data(self) -> dict[str]:
        return self._questions


@qtbridge(module="QuizModel")
def main():
    qa_model = QuestionModel()
    bridge_instance(qa_model, name="QA_model")


if __name__ == "__main__":
    main()
