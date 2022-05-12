import pandas
import pandas as pd
from deep_translator import GoogleTranslator
import csv


def get_translate(text, source_lang="de", target_lang="en"):

    translator = GoogleTranslator(source=source_lang, target=target_lang)

    try:
        result = translator.translate(text)
    except Exception:
        print(f"Translation failed with text: {text}")
        result = None

    if (result is None) or (len(result) == 0):
        output = {
            source_lang: None,
            target_lang: None
        }

    else:
        output = {
            source_lang: text,
            target_lang: result
        }
    return output


def add_translate(data, output_file, text_var="description_de",
                  source_lang="de", target_lang="en"):

    if hasattr(data, text_var):
        text = data[text_var]
    else:
        raise ValueError("Missing text variable in input data.")

    try:
        output = pd.read_csv(output_file)
        text_done = output[source_lang]
    except Exception:
        print("No translate output file. Generating new...")
        text_done = []

    # select unique texts, then subset leftover
    text = list(set(text))
    text_left = list(set(text).difference(text_done))
    results = []

    print(f"{len(text)} unique texts. "
          f"{len(text_left)} left to translate...")

    with open(output_file, "a+", newline="\n") as csv_output:

        # header
        cols = [source_lang, target_lang]
        writer = csv.DictWriter(
            csv_output, delimiter=",", lineterminator="\n", fieldnames=cols
        )

        # add header if file does not exist
        if csv_output.tell() == 0:
            writer.writeheader()

        # append each translation to csv
        for t in text_left:
            t_trans = get_translate(t, source_lang, target_lang)
            results.append(t_trans)
            writer.writerow(t_trans)

            # Print status every 100 texts
            if len(results) % 100 == 0:
                print(f"Completed {len(results)} of {len(text_left)} texts")

        if len(results) == len(text_left):
            print(f"Finished translating all {len(text_left)} texts.")
            print(f"Merging translated text to data")
            translates = pd.read_csv(output_file).rename(
                columns={"de": "description_de", "en": "description_en"})
            data = data.merge(translates, how="left", on="description_de")
            return data
