import io
import re

import streamlit as st
from docx import Document
from pypdf import PdfReader

st.set_page_config(
    page_title="Raremotion Document AI",
    page_icon="📄",
    layout="wide",
)

st.title("📄 Raremotion Document AI")
st.caption("Intelligent Document Processing | Raremotion Labs")


def extract_text(uploaded_file):
    file_bytes = uploaded_file.getvalue()

    if uploaded_file.name.lower().endswith(".pdf"):
        reader = PdfReader(io.BytesIO(file_bytes))
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    if uploaded_file.name.lower().endswith(".docx"):
        document = Document(io.BytesIO(file_bytes))
        paragraphs = [p.text for p in document.paragraphs]
        for table in document.tables:
            for row in table.rows:
                paragraphs.append(" | ".join(cell.text for cell in row.cells))
        return "\n".join(paragraphs)

    return ""


uploaded_file = st.file_uploader(
    "Upload a PDF or Word document",
    type=["pdf", "docx"],
)

if uploaded_file:
    try:
        text = extract_text(uploaded_file)

        if not text.strip():
            st.warning("No readable text found in this document.")
            st.stop()

        words = text.split()
        sentences = [
            s.strip() for s in re.split(r"(?<=[.!?])\s+", text)
            if s.strip()
        ]

        col1, col2, col3 = st.columns(3)
        col1.metric("Words", len(words))
        col2.metric("Characters", len(text))
        col3.metric("Sentences", len(sentences))

        st.subheader("Document Preview")
        st.text_area("Extracted Text", text, height=300)


        st.subheader("Document Summary")

        from collections import Counter

        stopwords = {
            "the", "and", "for", "with", "from", "that",
            "this", "have", "are", "was", "were", "into",
            "your", "their", "about", "through", "using",
        }

        frequencies = Counter(
            word.lower()
            for word in re.findall(r"[a-zA-Z]{3,}", text)
            if word.lower() not in stopwords
        )

        ranked = []
        for index, sentence in enumerate(sentences):
            if len(sentence.split()) < 5:
                continue

            # Exclude lines containing common contact details.
            if re.search(
                r"@|https?://|www\\.|\\b\\d{7,}\\b",
                sentence,
                re.IGNORECASE,
            ):
                continue

            terms = re.findall(r"[a-zA-Z]{3,}", sentence.lower())
            score = sum(frequencies[term] for term in terms)
            score = score / max(len(terms), 1)

            ranked.append((score, index, sentence))

        top = sorted(ranked, reverse=True)[:5]
        top.sort(key=lambda item: item[1])

        summary = " ".join(item[2] for item in top)

        if summary:
            st.info(summary)
        else:
            st.warning("Not enough suitable text to summarize.")


        st.subheader("Ask Your Document")
        question = st.text_input(
            "Ask a question about your document",
            placeholder="What programming languages are mentioned?",
        )

        if question:
            question_words = set(
                re.findall(r"[a-zA-Z]{3,}", question.lower())
            )
            question_words -= {
                "what", "which", "where", "when", "who",
                "how", "does", "the", "are", "and",
                "about", "mentioned", "document",
            }

            passages = [
                line.strip()
                for line in text.splitlines()
                if line.strip()
            ]

            results = []
            for passage in passages:
                passage_words = set(
                    re.findall(r"[a-zA-Z]{3,}", passage.lower())
                )
                score = len(question_words & passage_words)
                if score > 0:
                    results.append((score, passage))

            results.sort(key=lambda item: item[0], reverse=True)

            if results:
                st.success("Relevant information found:")
                for _, passage in results[:3]:
                    st.write(passage)
            else:
                st.warning("No relevant information found.")

        st.subheader("Search Document")
        keyword = st.text_input("Enter a keyword")

        if keyword:
            matches = [
                line.strip()
                for line in text.splitlines()
                if keyword.lower() in line.lower()
            ]
            st.write(f"Found {len(matches)} matching lines.")
            for match in matches[:20]:
                st.write(match)

        st.download_button(
            "Download Extracted Text",
            text,
            file_name="raremotion_extracted_text.txt",
            mime="text/plain",
        )

    except Exception as error:
        st.error(f"Unable to process this document: {error}")

st.divider()
st.caption("© Raremotion Labs")

        # Document summary will be integrated into the main
        # upload-processing section in the next step.
