
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import pandas as pd

APP_DIR = Path(__file__).resolve().parent
DEFAULT_FILE = APP_DIR / "students.parquet"

DATA_COLUMNS = [
    "Фамилия и инициалы",
    "Номер группы",
    "Математика",
    "Программирование",
    "Базы данных",
    "Дата добавления",
]
SUBJECT_COLUMNS = ["Математика", "Программирование", "Базы данных"]
GRADE_MIN = 2
GRADE_MAX = 5


class IndividualApp:
    """Tkinter application for managing student performance data."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Успеваемость студентов")
        self.root.geometry("1100x650")

        self.file_path_var = tk.StringVar(value=str(DEFAULT_FILE))
        self.fio_var = tk.StringVar()
        self.group_var = tk.StringVar()
        self.math_var = tk.StringVar()
        self.programming_var = tk.StringVar()
        self.databases_var = tk.StringVar()
        self.delete_column_var = tk.StringVar(value=DATA_COLUMNS[0])
        self.delete_value_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Готово")

        self.students = self.load_students(DEFAULT_FILE)

        self.create_widgets()
        self.refresh_table(self.students)

    def create_widgets(self) -> None:
        """Create all graphical interface widgets."""
        file_frame = ttk.LabelFrame(self.root, text="Файл Parquet")
        file_frame.pack(fill="x", padx=10, pady=6)

        file_entry = ttk.Entry(
            file_frame,
            textvariable=self.file_path_var,
        )
        file_entry.pack(side="left", fill="x", expand=True, padx=6, pady=6)

        ttk.Button(
            file_frame,
            text="Выбрать",
            command=self.choose_file,
        ).pack(side="left", padx=4)
        ttk.Button(
            file_frame,
            text="Загрузить",
            command=self.load_from_selected_file,
        ).pack(side="left", padx=4)
        ttk.Button(
            file_frame,
            text="Сохранить",
            command=self.save_to_selected_file,
        ).pack(side="left", padx=4)
        ttk.Button(
            file_frame,
            text="Проверить Parquet",
            command=self.validate_selected_file,
        ).pack(side="left", padx=4)

        input_frame = ttk.LabelFrame(self.root, text="Добавление студента")
        input_frame.pack(fill="x", padx=10, pady=6)

        fields = [
            ("Фамилия и инициалы", self.fio_var),
            ("Номер группы", self.group_var),
            ("Математика", self.math_var),
            ("Программирование", self.programming_var),
            ("Базы данных", self.databases_var),
        ]

        for index, (label, variable) in enumerate(fields):
            ttk.Label(input_frame, text=label).grid(
                row=0,
                column=index,
                padx=4,
                pady=2,
                sticky="w",
            )
            ttk.Entry(input_frame, textvariable=variable, width=22).grid(
                row=1,
                column=index,
                padx=4,
                pady=2,
                sticky="ew",
            )
            input_frame.columnconfigure(index, weight=1)

        ttk.Button(
            input_frame,
            text="Добавить",
            command=self.add_student,
        ).grid(row=1, column=len(fields), padx=4, pady=2)
        ttk.Button(
            input_frame,
            text="Очистить поля",
            command=self.clear_input_fields,
        ).grid(row=1, column=len(fields) + 1, padx=4, pady=2)

        action_frame = ttk.LabelFrame(self.root, text="Действия")
        action_frame.pack(fill="x", padx=10, pady=6)

        ttk.Button(
            action_frame,
            text="Показать всех",
            command=self.show_all_students,
        ).pack(side="left", padx=5, pady=6)
        ttk.Button(
            action_frame,
            text="Средний балл > 4.0",
            command=self.show_successful_students,
        ).pack(side="left", padx=5, pady=6)

        ttk.Label(action_frame, text="Удалить по колонке:").pack(
            side="left",
            padx=(20, 5),
        )
        ttk.Combobox(
            action_frame,
            values=DATA_COLUMNS,
            textvariable=self.delete_column_var,
            width=22,
            state="readonly",
        ).pack(side="left", padx=5)
        ttk.Entry(
            action_frame,
            textvariable=self.delete_value_var,
            width=24,
        ).pack(side="left", padx=5)
        ttk.Button(
            action_frame,
            text="Удалить",
            command=self.delete_rows_by_column,
        ).pack(side="left", padx=5)

        table_frame = ttk.Frame(self.root)
        table_frame.pack(fill="both", expand=True, padx=10, pady=6)

        self.tree = ttk.Treeview(table_frame, show="headings")
        vertical_scroll = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.tree.yview,
        )
        horizontal_scroll = ttk.Scrollbar(
            table_frame,
            orient="horizontal",
            command=self.tree.xview,
        )
        self.tree.configure(
            yscrollcommand=vertical_scroll.set,
            xscrollcommand=horizontal_scroll.set,
        )

        self.tree.grid(row=0, column=0, sticky="nsew")
        vertical_scroll.grid(row=0, column=1, sticky="ns")
        horizontal_scroll.grid(row=1, column=0, sticky="ew")
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        ttk.Label(
            self.root,
            textvariable=self.status_var,
            anchor="w",
        ).pack(fill="x", padx=10, pady=(0, 8))

    def choose_file(self) -> None:
        """Open a file dialog and select a Parquet file."""
        selected_path = filedialog.asksaveasfilename(
            defaultextension=".parquet",
            filetypes=[("Parquet files", "*.parquet"), ("All files", "*.*")],
            initialdir=str(APP_DIR),
            title="Выберите или создайте Parquet-файл",
        )
        if selected_path:
            self.file_path_var.set(selected_path)

    def load_students(self, path: Path) -> pd.DataFrame:
        """Load students from Parquet or return an empty DataFrame."""
        if not path.exists():
            return pd.DataFrame(columns=DATA_COLUMNS)

        try:
            students = pd.read_parquet(path, engine="pyarrow")
        except ImportError as error:
            self.show_pyarrow_error(error)
            return pd.DataFrame(columns=DATA_COLUMNS)
        except Exception as error:
            messagebox.showerror("Ошибка чтения", str(error))
            return pd.DataFrame(columns=DATA_COLUMNS)

        return self.prepare_students(students)

    @staticmethod
    def prepare_students(students: pd.DataFrame) -> pd.DataFrame:
        """Normalize columns, numeric values and sort by group number."""
        result = students.reindex(columns=DATA_COLUMNS).copy()

        if result.empty:
            return result

        numeric_columns = ["Номер группы", *SUBJECT_COLUMNS]
        for column in numeric_columns:
            result[column] = pd.to_numeric(result[column], errors="raise")

        return result.sort_values(
            by=["Номер группы", "Фамилия и инициалы"],
            ascending=[True, True],
        ).reset_index(drop=True)

    def save_students(self) -> bool:
        """Save current DataFrame to the selected Parquet file."""
        path = Path(self.file_path_var.get())
        path.parent.mkdir(parents=True, exist_ok=True)

        try:
            prepared_students = self.prepare_students(self.students)
            prepared_students.to_parquet(path, engine="pyarrow", index=False)
        except ImportError as error:
            self.show_pyarrow_error(error)
            return False
        except Exception as error:
            messagebox.showerror("Ошибка сохранения", str(error))
            return False

        self.students = prepared_students
        self.status_var.set(f"Данные сохранены: {path}")
        return True

    def load_from_selected_file(self) -> None:
        """Load data from the selected file and show it in the table."""
        path = Path(self.file_path_var.get())
        self.students = self.load_students(path)
        self.refresh_table(self.students)
        self.status_var.set(f"Загружено строк: {len(self.students)}")

    def save_to_selected_file(self) -> None:
        """Save data using the selected path."""
        if self.save_students():
            self.refresh_table(self.students)
            messagebox.showinfo("Сохранение", "Данные успешно сохранены.")

    def validate_selected_file(self) -> None:
        """Validate that the selected Parquet file is readable."""
        path = Path(self.file_path_var.get())

        if not path.exists():
            messagebox.showwarning("Проверка", "Файл еще не создан.")
            return

        try:
            students = pd.read_parquet(path, engine="pyarrow")
        except ImportError as error:
            self.show_pyarrow_error(error)
            return
        except Exception as error:
            messagebox.showerror("Проверка", f"Ошибка чтения: {error}")
            return

        missing_columns = [
            column for column in DATA_COLUMNS if column not in students.columns
        ]
        if missing_columns:
            messagebox.showerror(
                "Проверка",
                "Отсутствуют столбцы: " + ", ".join(missing_columns),
            )
            return

        messagebox.showinfo(
            "Проверка",
            "Файл Parquet корректен. "
            f"Строк: {len(students)}, столбцов: {len(students.columns)}.",
        )

    def add_student(self) -> None:
        """Validate input values and add a new student row."""
        try:
            student = self.get_student_from_form()
        except ValueError as error:
            messagebox.showwarning("Проверка данных", str(error))
            return

        self.students = pd.concat(
            [self.students, pd.DataFrame([student])],
            ignore_index=True,
        )
        self.students = self.prepare_students(self.students)

        if self.save_students():
            self.refresh_table(self.students)
            self.clear_input_fields()
            messagebox.showinfo("Добавление", "Студент добавлен.")

    def get_student_from_form(self) -> dict[str, object]:
        """Read and validate one student record from input fields."""
        fio = self.fio_var.get().strip()
        if not fio:
            raise ValueError("Введите фамилию и инициалы студента.")

        group_number = self.parse_positive_int(
            self.group_var.get(),
            "Номер группы",
        )
        math_grade = self.parse_grade(self.math_var.get(), "Математика")
        programming_grade = self.parse_grade(
            self.programming_var.get(),
            "Программирование",
        )
        databases_grade = self.parse_grade(
            self.databases_var.get(),
            "Базы данных",
        )

        return {
            "Фамилия и инициалы": fio,
            "Номер группы": group_number,
            "Математика": math_grade,
            "Программирование": programming_grade,
            "Базы данных": databases_grade,
            "Дата добавления": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    @staticmethod
    def parse_positive_int(value: str, field_name: str) -> int:
        """Convert a string to a positive integer."""
        try:
            number = int(value)
        except ValueError as error:
            message = f"Поле '{field_name}' должно быть целым числом."
            raise ValueError(message) from error

        if number <= 0:
            raise ValueError(f"Поле '{field_name}' должно быть больше нуля.")
        return number

    @staticmethod
    def parse_grade(value: str, field_name: str) -> int:
        """Convert a string to a grade and validate its range."""
        try:
            grade = int(value)
        except ValueError as error:
            message = f"Оценка '{field_name}' должна быть целым числом."
            raise ValueError(message) from error

        if not GRADE_MIN <= grade <= GRADE_MAX:
            raise ValueError(
                f"Оценка '{field_name}' должна быть от {GRADE_MIN} до {GRADE_MAX}."
            )
        return grade

    def show_all_students(self) -> None:
        """Display all student records."""
        self.refresh_table(self.students)
        self.status_var.set(f"Показаны все записи: {len(self.students)}")

    def show_successful_students(self) -> None:
        """Show students whose average grade is greater than 4.0."""
        if self.students.empty:
            messagebox.showinfo("Результат", "Данные отсутствуют.")
            return

        students = self.prepare_students(self.students).copy()
        students["Средний балл"] = students[SUBJECT_COLUMNS].mean(axis=1)
        selected_students = students.loc[
            students["Средний балл"] > 4.0,
            ["Фамилия и инициалы", "Номер группы", "Средний балл"],
        ]

        if selected_students.empty:
            self.refresh_table(selected_students)
            messagebox.showinfo(
                "Результат",
                "Нет студентов со средним баллом выше 4.0.",
            )
            return

        self.refresh_table(selected_students)
        self.status_var.set(
            "Показаны студенты со средним баллом выше 4.0: "
            f"{len(selected_students)}"
        )

    def delete_rows_by_column(self) -> None:
        """Delete all rows where the chosen column equals the given value."""
        column = self.delete_column_var.get()
        value = self.delete_value_var.get().strip()

        if not value:
            messagebox.showwarning("Удаление", "Введите значение для удаления.")
            return

        if column not in self.students.columns:
            messagebox.showerror("Удаление", f"Столбец '{column}' не найден.")
            return

        old_length = len(self.students)
        mask = self.students[column].astype(str) != value
        self.students = self.students.loc[mask].reset_index(drop=True)
        deleted_count = old_length - len(self.students)

        if self.save_students():
            self.refresh_table(self.students)
            self.status_var.set(f"Удалено строк: {deleted_count}")
            messagebox.showinfo("Удаление", f"Удалено строк: {deleted_count}")

    def refresh_table(self, data: pd.DataFrame) -> None:
        """Refresh the Treeview widget with DataFrame content."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        columns = list(data.columns)
        self.tree["columns"] = columns

        for column in columns:
            self.tree.heading(column, text=column)
            self.tree.column(column, width=160, minwidth=80, stretch=True)

        for _, row in data.iterrows():
            values = ["" if pd.isna(value) else value for value in row]
            self.tree.insert("", "end", values=values)

    def clear_input_fields(self) -> None:
        """Clear all input fields for adding a student."""
        self.fio_var.set("")
        self.group_var.set("")
        self.math_var.set("")
        self.programming_var.set("")
        self.databases_var.set("")

    @staticmethod
    def show_pyarrow_error(error: ImportError) -> None:
        """Show an explanation when Parquet dependencies are missing."""
        messagebox.showerror(
            "Не установлен pyarrow",
            "Для работы с Parquet установите пакет pyarrow:\n"
            "python -m pip install pyarrow\n\n"
            f"Подробности: {error}",
        )


def main() -> None:
    """Run the Tkinter application."""
    root = tk.Tk()
    app = IndividualApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

