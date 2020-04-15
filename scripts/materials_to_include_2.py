"""
Convert raw experimental materials to a full experimental spec.
"""

from argparse import ArgumentParser
from collections import defaultdict
import json
import re
from pathlib import Path


# Quote JSON keys that are missing quotes.
MISSING_QUOTE_RE = re.compile(r"(\"(.*?)\"|(\w+))(\s*:\s*(\".*?\"|.))")


DATA_INCLUDE_TEMPLATE = """

var materials_by_tag = {materials_by_tag};

var showProgressBar = false;

var code = Math.floor(Math.random()*100000000);
var sendingResultsMessage = "The results are now being transferred.  Please wait.";
var completionMessage = "Thank you for your participation.  The results were successfully transmitted.  Your participation code is: " + code.toString();
var completionErrorMessage = "The transmission of the results failed.  Please contact jgauthie@mit.edu and retry the transmission again by clicking the link.  Your participation code is: " + code.toString();

var items = [
    ["welcome", "Message", {{html:'<table width="100%"><tr><td valign="top" align="right">Department of Brain and Cognitive Sciences<br>Massachusetts Institute of Technology<br>77 Massachusetts Avenue<br>Cambridge, MA 02139-4307, USA</tr></table>\
      <h2>Thank you very much for your participation!</h2><p>This task is part of a MIT scientific research project. Your decision to complete this task is voluntary. There is no way for us to identify you. The only information we will have, in addition to your responses, is the time at which you completed the survey. The results of the research may be presented at scientific meetings or published in scientific journals. Clicking on the link below indicates that you are at least 18 years of age and agree to complete this task voluntarily.'}}],
    ["intro-maze", "Message", {{html: "<p>For this experiment, please place your left index finger on the 'e' key and your right index finger on the 'i' key.</p><p> You will read sentences word by word. On each screen you will see two options: one will be the next word in the sentence, and one will not. Select the word that continues the sentence by pressing 'e' (left-hand) for the word on the left or pressing 'i' (right-hand) for the word on the right.</p><p>Select the best word as quickly as you can, but without making too many errors.</p>"}}],
    ["instructions2", "Message", {{html:'Now please answer a couple of questions about your background.  In accordance with the ethics guidelines of the Massachusetts Institute of Technology, this information will be stored in anonymous form and it will be impossible to link it to you.'}}],
    ["debriefing", "Message", {{html:"<p>Thank you.  You will receive the participation code on the next page.</p>\n\n<p>Purpose of this study (feel free to skip): We’re generally interested in how the human brain processes language. The present study is testing out a new method for studying what types of sentence constructions are easier or harder to read. We're also interested in whether it's easy to understand and remember text read with this method. Your data will help us to answer these questions.</p>"}}],

    ["questionnaire", "Form", {{html:'How old are you? <input type="text" name="age" size="2" maxlength="2" autofocus="true"/>'}}],
    ["questionnaire", "Question", {{q:"Please select your gender.", as:["Male", "Female","Non-binary", "Decline to state"], hasCorrect: false}}],
    ["questionnaire", "Form", {{html:'What is your native language? <input type="text" name="native" size="10" maxlength="50" autofocus="true"/>'}}],
    ["questionnaire", "Form", {{html:'Thank you for completing the experiment. Very briefly, what do you think this study is about?<br/><textarea name="topic" rows="3" cols="50" autofocus="true"></textarea>'}}],
    ["questionnaire", "Form", {{html:'How was your experience doing this task? What strategies did you use?<br/><textarea name="strategy" rows="3" cols="50" autofocus="true"></textarea>'}}],
    ["questionnaire", "Form", {{html:'What do you think fair pay for this task would be?<input type="text" name="pay" size="10" maxlength="20" autofocus="true"/>'}}],

    ["intro-practice", "Message", {{html: "The following items are for practice." }}],
    ["end-practice", "Message", {{html: "End of practice. The experiment will begin next."}}],
    [["practice", 104], "Maze", {{s:"The therapist set up a meeting with the upset woman and her husband yesterday.", a:"x-x-x socialism ten sit sum absence wave ran keeps exist dry sum settled remainder.", redo: true}}],

    ["sep", "MazeSeparator", {{normalMessage: "Correct! Press any key to continue", errorMessage: "Incorrect! Press any key to continue."}}],

    ["done", "Message", {{html: "All done!"}}],
];

// Sample a collection of experimental items.
var total_items = {items_per_subject};

var tag_sizes = _.map(materials_by_tag, function(v) {{ return v.length  }});
var samples = _.mapValues(materials_by_tag, function(items, tag) {{
  var sample_size = Math.floor(items.length / _.sum(tag_sizes) * total_items);
  return _.sampleSize(items, sample_size)
}});
var samples_flat = _.flatten(_.concat(_.values(samples)));

// Now concatenate to the existing items array.
items = items.concat(samples_flat);

//for G-maze
var shuffleSequence = seq("welcome", "intro-maze", "intro-practice", anyOf("practice"), "end-practice",
                          followEachWith("sep", {items_selector}),
                          "instructions2", anyOf("questionnaire"), "debriefing");
"""


def main(args):
    all_conditions = set()
    materials_by_tag = defaultdict(list)

    for materials_txt in args.materials_dir.glob("*.txt"):
        exp_name = materials_txt.stem
        exp_tag = exp_name.split("_")[0]

        with materials_txt.open("r") as f:
            for line in f:
                if line.strip():
                    line = MISSING_QUOTE_RE.sub(r'"\2\3"\4', line.strip().rstrip(","))
                    line = json.loads(line)
                    line_condition, _ = line[0]

                    # Add "redo" flag
                    line[2]["redo"] = True

                    all_conditions.add(line_condition)
                    materials_by_tag[exp_tag].append(line)

    # Prepare an ibex expression that identifies all of the experimental
    # items -- by selecting the relevant condition lines
    items_selector = "randomize(anyOf(" + ", ".join(f"startsWith(\"{condition}\")" for condition in all_conditions) + "))"

    out = DATA_INCLUDE_TEMPLATE.format(items_selector=items_selector,
                                       materials_by_tag=json.dumps(materials_by_tag),
                                       items_per_subject=args.items_per_subject)
    with (args.out_path).open("w") as out_f:
        out_f.write(out)


if __name__ == "__main__":
    p = ArgumentParser()
    p.add_argument("--materials_dir", type=Path, default="materials")
    p.add_argument("--out_path", type=Path, default="data_includes/experiment.js")
    p.add_argument("-n", "--items_per_subject", type=int, default=115)

    main(p.parse_args())
