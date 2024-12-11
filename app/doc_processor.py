import os
import re
import requests
from bs4 import BeautifulSoup
from docx import Document

def process_docx_to_md(docx_path: str, output_md_path: str) -> None:
    if not os.path.exists(docx_path):
        raise FileNotFoundError(f"Файл {docx_path} не найден.")

    document = Document(docx_path)
    text = "\n".join(para.text for para in document.paragraphs)

    url_pattern = r"https?://[^\s]+"
    urls = re.findall(url_pattern, text)

    if not urls:
        raise ValueError("Ссылки не найдены в документе.")

    word_count = 0
    with open(output_md_path, "w", encoding="utf-8") as md_file:
        for url in urls:
            try:
                response = requests.get(url)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "html.parser")
                page_text = soup.get_text(separator=" ", strip=True)
                md_file.write(page_text + "\n\n")
                word_count += len(page_text.split())

                if word_count >= 1000:
                    md_file.write(" " * 10 + "следующая страница\n\n")
                    word_count = 0

            except Exception as e:
                print(f"Ошибка при обработке {url}: {e}")

    print(f"Текст успешно сохранён в {output_md_path}")
