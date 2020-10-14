import argparse
import os
from os import listdir
from os.path import isfile, join
import re
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument("--version", type=str, help="choose from easy, medium, medium+, and hard")
parser.add_argument("--dataset", type=str, help="choose dataset from all, or 1 of 8 datasets: cnndm, gigaword, xsum, msnews, msqg, squadqg, coqa, personachat")
parser.add_argument("--split", type=str, default="test", help="choose test or valid")
parser.add_argument("--generated", type=str, help="generated output file.")
#parser.add_argument("--golden", type=str, help="Gold output file.")
args = parser.parse_args()

#fin = open(args.generated, 'r', encoding='utf-8')
#fgolden = open(args.golden, 'r', encoding='utf-8')

data_root_path='../data'

support_dataset=['cnndm', 'gigaword', 'xsum', 'msnews', 'squadqg', 'msqg', 'coqa', 'personachat']
files2rouge_template='.*ROUGE-1 Average_F: (?P<rouge1_f>\d+(\.\d*)?|\.\d+).*ROUGE-2 Average_F: (?P<rouge2_f>\d+(\.\d*)?|\.\d+).*ROUGE-L Average_F: (?P<rougeL_f>\d+(\.\d*)?|\.\d+).*'
qg_template='.*Bleu_4: (?P<bleu4>\d+(\.\d*)?|\.\d+).*METEOR: (?P<meteor>\d+(\.\d*)?|\.\d+).*ROUGE_L: (?P<rougeL>\d+(\.\d*)?|\.\d+).*'
personachat_template='.*?(?P<d1>[-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?).*?(?P<d2>[-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?).*Bleu_1: (?P<bleu1>\d+(\.\d*)?|\.\d+).*Bleu_2: (?P<bleu2>\d+(\.\d*)?|\.\d+).*'

def scale_up(d):
   return {k:float(d[k])*100 for k in d.keys()}

def eval_one_dataset():
    golden_file=f"{data_root_path}/{args.version}/{args.dataset}_data/org_data/{args.split}.tgt"
    golden_src_file=f"{data_root_path}/{args.version}/{args.dataset}_data/org_data/{args.split}.src"

    eval_template = {
        'cnndm': f"python evaluate/cnndm/postprocess_cnn_dm.py --generated {generated_file} --golden {golden_file}",
        #'gigaword': f"files2rouge {generated_file} {golden_file}",
        'gigaword': f"python evaluate/gigaword/eval.py --pred {generated_file} --gold {golden_file}",
        'xsum': f"files2rouge {generated_file} {golden_file}",
        'msnews': f"files2rouge {generated_file} {golden_file}",
        'squadqg': f"python2 evaluate/qg/eval_on_unilm_qg.py --out {generated_file} --src {golden_src_file} --tgt {golden_file}",
        'msqg': f"python2 evaluate/qg/eval.py --out {generated_file} --src {golden_src_file} --tgt {golden_file}",
        'coqa': f"python evaluate/coqa/evaluate-v1.0.py --pred-file {generated_file} --golden-file {golden_file}",
        'personachat': f"python evaluate/distinct_metric.py {generated_file} -n 1 2 && python2 evaluate/qg/eval.py --out {generated_file} --src {golden_src_file} --tgt {golden_file}"
    }

    cmd=eval_template[args.dataset]
    #print(cmd)
    try:
        output=os.popen(cmd).read()
        if args.dataset in ['cnndm', 'gigaword', 'xsum', 'msnews']:
            d=re.search(files2rouge_template, output.replace("\n", " ")).groupdict()
            d=scale_up(d)
            print(f"{args.dataset}\trouge1/rouge2/rougeL\t{d['rouge1_f']:.2f}/{d['rouge2_f']:.2f}/{d['rougeL_f']:.2f}")
        elif args.dataset == 'squadqg' or args.dataset == 'msqg':
            d=re.search(qg_template, output.replace("\n", " ")).groupdict()
            d=scale_up(d)
            print(f"{args.dataset}\trougeL/bleu4/meteor\t{d['rougeL']:.2f}/{d['bleu4']:.2f}/{d['meteor']:.2f}")
        elif args.dataset == 'personachat':
            d=re.search(personachat_template, output.replace("\n", " ")).groupdict()
            d=scale_up(d)
            print(f"{args.dataset}\tbleu1/bleu2/distinct_1/distinct_2\t{d['bleu1']:.2f}/{d['bleu2']:.2f}/{d['d1']:.2f}/{d['d2']:.2f}")
        elif args.dataset == 'coqa':
            output=float(output)*100
            print(f"{args.dataset}\tf1\t{output:.2f}")
        else:
            print(output)
    except:
        print(f"{args.dataset} evaluate failed!")


if args.dataset != 'all':
    generated_file=args.generated
    eval_one_dataset()
else:
    output_root_path=args.generated
    onlyfolders = [f for f in listdir(output_root_path) if not isfile(join(args.generated, f))]
    for dataset in support_dataset:
        for folder in onlyfolders:
            if folder.startswith(dataset):
                for hypo_file in listdir(args.generated + '/' + folder):
                    if 'hypo' in hypo_file or 'score' in hypo_file:
                        generated_file=args.generated + '/' + folder + '/' + hypo_file
                        print(f"{dataset}\tpredict_file:{generated_file}")
                        args.dataset=dataset
                        args.gnerated=generated_file
                        eval_one_dataset()

