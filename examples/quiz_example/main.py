# Copyright (C) 2022 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR BSD-3-Clause

from QtBridge import bridge_instance, qtbridge


class QuestionModel:
    def __init__(self):
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
