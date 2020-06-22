import argparse
import string

from gensim.models.doc2vec import Doc2Vec, TaggedDocument

from nltk import edit_distance
from nltk.tokenize import sent_tokenize
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize


def tokenize_ru(file_text):
    tokens = word_tokenize(file_text)
    tokens = [i for i in tokens if (i not in string.punctuation)]

    stop_words = stopwords.words("russian")
    stop_words.extend(["в", "к", "на", "..."])
    tokens = [i for i in tokens if (i not in stop_words)]
    tokens = [i.replace("«", "").replace("»", "") for i in tokens]
    tokens = [i.replace("`", "").replace("'", "") for i in tokens]
    return tokens


def find_similar(text_input, test_sents, output_file):
    result = []

    text = open(text_input, "r", encoding="utf-8").read()
    test_sents = open(test_sents, "r", encoding="utf-8").read()
    test_sents = test_sents.split("\n")

    sentences = [tokenize_ru(sent) for sent in sent_tokenize(text, "russian")]

    documents = [TaggedDocument(doc, [i]) for i, doc in enumerate(sentences)]

    model = Doc2Vec(documents, vector_size=5, window=2, min_count=1, workers=4)

    for sent in test_sents:
        sims = model.docvecs.most_similar(
            positive=[model.infer_vector(sent.split(" "))], topn=100
        )

        lev_dist = []
        for (idx, q) in sims:
            ev_sent = " ".join(sentences[idx])
            lev_dist.append((edit_distance(sent, ev_sent), ev_sent))

        lev_dist = sorted(lev_dist, key=lambda x: x[0])

        result.append(f"asr: {sent}\n" f"text: {lev_dist[0][1]}\n\n")

    with open(output_file, 'w') as file:
        for item in result:
            file.write(item)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Find similar text.")
    parser.add_argument("--text-input", type=str, help="Input TXT with source")
    parser.add_argument("--test-sents", type=str, help="Input sentencies to evaluate")
    parser.add_argument("--output-file", type=str, help="Result file")

    args = parser.parse_args()

    find_similar(
        text_input=args.text_input,
        test_sents=args.test_sents,
        output_file=args.output_file,
    )
