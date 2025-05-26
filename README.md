# SWE‑Dev: Evaluating and Training Autonomous Feature‑Driven Software Development

[![arXiv](https://img.shields.io/badge/arXiv-2505.16975-b31b1b.svg)](https://arxiv.org/abs/2505.16975)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE)
[![Kaggle](https://img.shields.io/badge/Kaggle-dataset-blue.svg)](https://www.kaggle.com/datasets/dorothydu/fdd-bench)



> **SWE‑Dev** is the **first large‑scale benchmark and training corpus** for **feature‑driven development (FDD)** — the real‑world task of adding new functionality to existing codebases.
> It ships **14 000 training** and **500 test** tasks, each with a **runnable environment** and **developer‑written unit tests**, enabling both *supervised fine‑tuning* and *reinforcement learning from executable rewards*.

[📄 Dataset Overview](assets/overview.pdf)

---

## ✨ Highlights

* **Real‑world FDD tasks** drawn from mature open‑source projects.
* **End‑to‑end reproducibility** – every task bundles source, deps, Dockerfile & tests.
* **RL‑ready** – deterministic pass/fail reward signals from pytest.
* **Challenging** – Claude‑3.7‑Sonnet reaches only **22.45 % Pass\@3** on the *hard* split.
* **Effective for model improvement** – fine‑tuning a 7 B model on SWE‑Dev yields GPT‑4o‑level performance on hard split.

---

## Getting Started

### 1. Installation

```bash
conda create -n swe-dev python=3.12.0

# bleeding‑edge
git clone https://github.com/DorothyDUUU/SWE-Dev-dataset.git
cd SWE-Dev-dataset
pip install -r requirements.txt
```
### 2. Download the dataset

```bash
python scripts/download_data.py --dest ./data
```

The script organises the dataset as:

```
data/
 ├── train/
 │   ├── level1/
 │   ├── level2/
 │   └── level3/
 └── test/
     ├── Easy/
     └── Hard/
```

### 3. Quick evaluation

```bash
swe_dev.evaluate \
  --model meta-llama/Meta-Llama-3.1-8B-Instruct \
  --split hard \
  --backend vllm \
  --results_dir ./results
```

**Tip:** Set `--split hard` to benchmark on the *hard* subset only.

### 4. Fine‑tuning

1. Single-Agent SFT
```bash
swe_dev.train \
  --model mistralai/Mixtral-8x7B-v0.1 \
  --train_dir ./data/train \
  --output_dir ./checkpoints/mixtral_swe-dev \
  --lr 1e-5 --epochs 3 --fp16
```
2. Single-Agent RL
3. Multi-Agent SFT

---

## Leaderboard

We maintain an **ongoing leaderboard** at **<link coming soon>** covering:

| Category            | #Methods | Easy Best Pass\@1 | Hard Best Pass\@1 |
| ------------------- | -------- | ----------------- | ----------------- |
| Chat LLMs           | 17       | 54.37 %           | 19.13 %           |
| Reasoning LLMs      | 10       | 51.21 %           | 22.51 %           |
| Multi‑Agent Systems | 10       | -                 | -                 |

---

## News
[20250522] Release the preprint version! See the [preprint](https://www.arxiv.org/pdf/2505.16975).

---

## Citation

If you use SWE‑Dev, please cite:

```bibtex
@article{du2025swedev,
  title={SWE-Dev: Evaluating and Training Autonomous Feature-Driven Software Development},
  author={Du, Yaxin and Cai, Yuzhu and Zhou, Yifan and Wang, Cheng and Qian, Yu and Pang, Xianghe and Liu, Qian and Hu, Yue and Chen, Siheng},
  journal={arXiv preprint arXiv:2505.16975},
  year={2025}
}
```

---
## License

Code and dataset are released under the **Apache 2.0** license.
See the [LICENSE](LICENSE) file for details.

## Acknowledgements

