# Quiz Example

This example provides read-only access to a list of "developer jokes" stored in Python, allowing
QML to display the data.

## Functionality

- Stores a static list of joke questions and answers
- Exposes the data to QML as a table-like model (rows × 2 columns)
- Provides a getItem(row, column) accessor to retrieve specific fields
- QML implementation:
    - Picks a random question
    - Shows question text
    - Reveals the answer when the user presses a button
    - Loads another random question

## Purpose

This example demonstrates how to expose structured Python data to QML using `bridge_instance()`.

## Key Concepts

### 1. Exposing a Python Instance to QML

In the Python backend (`main.py`):

```python

from QtBridge import bridge_instance, qtbridge

class QuestionModel:
    def __init__(self):
        self._questions = [
            ...
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

```

The `bridge_instance(qa_model, name="QA_model")` call makes the Python object available in QML as
`QA_model`. This allows QML to:
- To access the directly in QML
- To be able to call `getItem()` method for retrieving specific item in the table

### 2. Using the Python Instance in QML

```qml
import backend 1.0

ApplicationWindow {
    visible: true
    property int currentIndex: Math.floor(Math.random() * QA_model.rowCount())
    property bool showingAnswer: false
    ColumnLayout {
        Rectangle {
            Text {
                id: displayText
                text: QA_model.getItem(currentIndex, 0)
            }
        }

        Button {
            id: actionButton
            text: showingAnswer ? "Another One" : "See Answer"

            onClicked: {
                if (!showingAnswer) {
                    displayText.text = QA_model.getItem(currentIndex, 1)
                    showingAnswer = true
                } else {
                    currentIndex = Math.floor(Math.random() * QA_model.rowCount())
                    displayText.text = QA_model.getItem(currentIndex, 0)
                    showingAnswer = false
                }
            }
        }
    }
}
```

## Running the Example

```bash
python main.py
```
