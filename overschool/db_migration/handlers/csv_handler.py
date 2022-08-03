import csv


class CSVHandler:
    def load_from(self, file_path: str):
        with open(file_path, "r", newline="", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file, delimiter=";")
            for row in reader:
                yield row
