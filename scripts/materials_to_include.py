"""
Convert raw experimental materials to a full experimental spec.
"""

from argparse import ArgumentParser
import json
from pathlib import Path


DATA_INCLUDE_TEMPLATE = """
//for G-maze
var shuffleSequence = seq("intro-gram", "intro-practice",
                          followEachWith("sep", "practice"),
                          "end-practice",
                          followEachWith("sep",{items_selector}),
                          "instructions2");

var showProgressBar =false;

var defaults = [
   // "Maze", {{redo: true}}, //uncomment to try "redo" mode
];
var items = [
	["instructions2", "Message", {{html:'End of sample Maze experiment.'}}],
	["intro-gram", "Message", {{html: "<p>For this experiment, please place your left index finger on the 'e' key and your right index finger on the 'i' key.</p><p> You will read sentences word by word. On each screen you will see two options: one will be the next word in the sentence, and one will not. Select the word that continues the sentence by pressing 'e' (left-hand) for the word on the left or pressing 'i' (right-hand) for the word on the right.</p><p>Select the best word as quickly as you can, but without making too many errors.</p>"}}],
	["intro-practice", "Message", {{html: "The following items are for practice." }}],
	["end-practice", "Message", {{html: "End of practice. The experiment will begin next."}}],

	["sep", "MazeSeparator", {{normalMessage: "Correct! Press any key to continue", errorMessage: "Incorrect! Press any key to continue."}}],

	["done", "Message", {{html: "All done!"}}],

        {items}
];
"""


def main(args):
    for materials_json in args.materials_dir.glob("*.json"):
        with materials_json.open("r") as f:
            items = json.load(f)

        # Prepare an ibex expression that identifies all of the experimental
        # items -- by selecting the relevant condition lines
        all_conditions = set(line[0][0] for line in items)
        items_selector = "randomize(anyOf(" + ", ".join(f"startsWith(\"{condition}\")" for condition in all_conditions) + "))"

        items = ",\n".join(json.dumps(item) for item in items)

        out = DATA_INCLUDE_TEMPLATE.format(items_selector=items_selector, items=items)
        with (args.out_dir / f"{materials_json.stem}.js").open("w") as out_f:
            out_f.write(out)


if __name__ == "__main__":
    p = ArgumentParser()
    p.add_argument("--materials_dir", type=Path, default="materials")
    p.add_argument("--out_dir", type=Path, default="data_includes")

    main(p.parse_args())
